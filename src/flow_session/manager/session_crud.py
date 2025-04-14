"""
工作流会话CRUD操作处理

提供工作流会话的创建、读取、更新和删除功能。
"""

import json
import uuid
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.db import FlowSession


class SessionCRUDMixin:
    """会话CRUD操作混入类"""

    def create_session(
        self,
        workflow_id: str,
        session_name: Optional[str] = None,
        task_id: Optional[str] = None,
        name: Optional[str] = None,
        flow_type: Optional[str] = None,
    ) -> FlowSession:
        """创建新的工作流会话

        Args:
            workflow_id: 工作流ID
            session_name: 会话名称
            task_id: 关联的任务ID
            name: 会话名称 (兼容参数)
            flow_type: 工作流类型

        Returns:
            新创建的会话对象

        Raises:
            ValueError: 如果找不到指定ID的工作流
        """
        # 检查工作流是否存在
        self._log("log_info", f"尝试创建工作流会话，workflow_id={workflow_id}")

        # 调试信息：列出所有工作流
        all_workflows = self.workflow_repo.get_all()
        self._log("log_info", f"数据库中有 {len(all_workflows)} 个工作流定义")
        for wf in all_workflows:
            self._log("log_info", f"  - ID: {wf.id}, 名称: {wf.name}")

        # 1. 尝试直接通过ID查找工作流
        workflow = self.workflow_repo.get_by_id(workflow_id)

        # 2. 如果找不到，尝试通过名称查找
        if not workflow:
            self._log("log_info", f"通过ID找不到工作流 {workflow_id}，尝试通过名称查找")
            workflow = self.workflow_repo.get_by_name(workflow_id)

            if workflow:
                self._log("log_info", f"通过名称找到工作流: {workflow.name}，ID: {workflow.id}")
                # 更新workflow_id为实际的ID
                workflow_id = workflow.id
            else:
                self._log("log_error", f"找不到ID或名称为 {workflow_id} 的工作流")
                raise ValueError(f"找不到ID或名称为 {workflow_id} 的工作流，请确认工作流是否存在")

        # 生成唯一ID
        session_id = f"{workflow_id}-{uuid.uuid4().hex[:8]}"
        # 使用提供的名称或生成默认名称
        effective_name = session_name or name or f"{workflow.name or workflow_id}-{uuid.uuid4().hex[:4]}"

        # 准备上下文数据
        context = {}
        if task_id:
            context["task_id"] = task_id

        # 创建会话对象
        new_session = FlowSession(
            id=session_id,
            workflow_id=workflow_id,
            name=effective_name,
            status="ACTIVE",
            task_id=task_id,
            flow_type=flow_type or workflow.type,
            context=json.dumps(context),
            is_current=True,
        )

        try:
            # 清除其他会话的当前状态
            other_sessions = self.session.query(FlowSession).filter(FlowSession.is_current == True).all()
            for other in other_sessions:
                other.is_current = False
                self.session_repo.update(other.id, {"is_current": False})

            # 保存会话
            self.session.add(new_session)
            self.session.commit()

            # 设置为当前会话
            self._set_current_session(session_id)

            # 获取工作流的第一个阶段并设置为当前阶段
            if workflow.stages and len(workflow.stages) > 0:
                first_stage_id = workflow.stages[0].get("id")
                if first_stage_id:
                    # 设置当前阶段ID
                    new_session.current_stage_id = first_stage_id
                    self.session_repo.update(session_id, {"current_stage_id": first_stage_id})

                    # 同时更新上下文中的当前阶段
                    context_data = {"current_stage": first_stage_id}
                    self.update_session_context(session_id, context_data)

                    self._log("log_stage_set", f"已自动设置初始阶段: {first_stage_id}")

                    # 创建阶段实例
                    try:
                        from src.flow_session.stage.manager import StageInstanceManager

                        stage_manager = StageInstanceManager(self.session)

                        # 创建阶段实例
                        stage_data = {"stage_id": first_stage_id, "name": workflow.stages[0].get("name", f"阶段-{first_stage_id}")}
                        stage_instance = stage_manager.create_instance(session_id, stage_data)
                        self._log("log_info", f"为会话 {session_id} 创建了阶段实例: {stage_instance.id if stage_instance else 'Failed'}")
                    except Exception as e:
                        self._log("log_error", f"创建阶段实例失败: {str(e)}")

            # 如果有关联任务，设置为当前任务
            if task_id:
                try:
                    # 使用导入的TaskService来保持松耦合
                    from src.services.task import TaskService

                    task_service = TaskService()
                    task_service.set_current_task(task_id)
                    # 更新任务的current_session_id
                    task_service.update_task(task_id, {"current_session_id": session_id})
                except Exception as e:
                    self._log("log_session_error", f"设置任务关联失败: {e}")

            # 记录日志
            self._log("log_session_created", workflow_id, context)

            return new_session
        except IntegrityError as e:
            self.session.rollback()
            self._log("log_session_error", e)
            raise e

    def get_session(self, id_or_name: str) -> Optional[FlowSession]:
        """获取会话详情，支持通过ID或名称获取

        Args:
            id_or_name: 会话ID或名称

        Returns:
            会话对象或None
        """
        return self.session_repo.find_session_by_id_or_name(id_or_name)

    def list_sessions(self, status: Optional[str] = None, workflow_id: Optional[str] = None) -> List[FlowSession]:
        """列出会话，可按状态和工作流ID过滤

        Args:
            status: 会话状态
            workflow_id: 工作流ID

        Returns:
            会话列表
        """
        sessions = []
        if status and workflow_id:
            sessions = self.session_repo.get_by_workflow_and_status(workflow_id, status)
        elif status:
            sessions = self.session_repo.get_by_status(status)
        elif workflow_id:
            sessions = self.session_repo.get_by_workflow_id(workflow_id)
        else:
            sessions = self.session_repo.get_all()

        return sessions

    def update_session(self, id_or_name: str, data: Dict[str, Any]) -> Optional[FlowSession]:
        """更新会话数据，支持通过ID或名称更新

        Args:
            id_or_name: 会话ID或名称
            data: 更新数据

        Returns:
            更新后的会话对象或None

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        return self.session_repo.update(session.id, data)

    def delete_session(self, id_or_name: str) -> bool:
        """删除会话，支持通过ID或名称删除

        Args:
            id_or_name: 会话ID或名称

        Returns:
            是否删除成功

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 如果删除的是当前会话，清除当前会话设置
        current_session = self.get_current_session()
        if current_session and current_session.id == session.id:
            self._clear_current_session()

        return self.session_repo.delete(session.id)
