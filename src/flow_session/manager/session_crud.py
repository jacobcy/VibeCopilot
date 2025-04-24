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
            workflow_id: 工作流ID或名称
            session_name: 会话名称
            task_id: 关联的任务ID
            name: 会话名称 (兼容参数)
            flow_type: 工作流类型

        Returns:
            新创建的会话对象

        Raises:
            ValueError: 如果找不到指定ID或名称的工作流
        """
        # 检查工作流是否存在
        self._log("log_info", f"尝试创建工作流会话，workflow_id={workflow_id}")

        # 使用改进的工作流搜索工具来查找工作流
        from src.workflow.utils.workflow_search import get_workflow_fuzzy

        workflow_dict = get_workflow_fuzzy(workflow_id)

        if not workflow_dict:
            # 调试信息：列出所有工作流
            all_workflows = self.workflow_repo.get_all()
            self._log("log_info", f"数据库中有 {len(all_workflows)} 个工作流定义")
            for wf in all_workflows:
                self._log("log_info", f"  - ID: {wf.id}, 名称: {wf.name}")

            self._log("log_error", f"找不到ID或名称为 {workflow_id} 的工作流")
            raise ValueError(f"找不到ID或名称为 {workflow_id} 的工作流，请确认工作流是否存在")

        # 获取实际的工作流ID
        actual_workflow_id = workflow_dict["id"]
        workflow_name = workflow_dict.get("name", "未命名工作流")
        self._log("log_info", f"已找到工作流: {workflow_name} (ID: {actual_workflow_id})")

        # 获取工作流对象
        workflow = self.workflow_repo.get_by_id(actual_workflow_id)
        if not workflow:
            # 尝试通过名称再次查找
            self._log("log_warning", f"通过ID({actual_workflow_id})找不到工作流对象，尝试通过名称查找")
            workflow = self.workflow_repo.get_by_name(workflow_name)

        if not workflow:
            # 如果仍然找不到，使用工作流定义信息继续创建会话
            self._log("log_warning", f"无法从数据库加载工作流对象，使用工作流定义信息创建会话")

        # 使用提供的名称或生成默认名称
        effective_name = session_name or name or f"{workflow_name}-会话"

        # 准备上下文数据
        context = {}
        if task_id:
            context["task_id"] = task_id

        try:
            # 使用Repository的方法创建会话
            # ID生成逻辑已经移动到Repository层
            new_session = self.session_repo.create_session(
                workflow_id=actual_workflow_id,
                name=effective_name,
                task_id=task_id,
                flow_type=flow_type or workflow_dict.get("type"),
                context=context,
            )

            # 设置为当前会话
            self._set_current_session(new_session.id)

            # 如果有关联任务，设置为当前任务
            if task_id:
                try:
                    # 使用导入的TaskService来保持松耦合
                    from src.services.task import TaskService

                    task_service = TaskService()
                    task_service.set_current_task(task_id)
                    # 更新任务的current_session_id
                    task_service.update_task(task_id, {"current_session_id": new_session.id})
                except Exception as e:
                    self._log("log_session_error", f"设置任务关联失败: {e}")

            # 记录日志
            self._log("log_session_created", actual_workflow_id, context)

            return new_session
        except Exception as e:
            self._log("log_session_error", e)
            raise ValueError(f"创建会话失败: {str(e)}")

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
            sessions = self.session_repo.get_by_workflow_and_status(self.session, workflow_id, status)
        elif status:
            sessions = self.session_repo.get_by_status(self.session, status)
        elif workflow_id:
            sessions = self.session_repo.get_by_workflow_id(self.session, workflow_id)
        else:
            sessions = self.session_repo.get_all(self.session)

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
