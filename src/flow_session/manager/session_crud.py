"""
工作流会话CRUD操作处理

提供工作流会话的创建、读取、更新和删除功能。
"""

import json
import logging
import uuid

logger = logging.getLogger(__name__)
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.db import FlowSession


class SessionCRUDMixin:
    """会话CRUD操作混入类"""

    def _get_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流定义

        Args:
            workflow_id: 工作流ID或名称

        Returns:
            工作流定义字典或None
        """
        from src.workflow.utils.workflow_search import get_workflow_fuzzy

        # 使用模糊匹配查找工作流
        workflow = get_workflow_fuzzy(workflow_id)
        return workflow

    def get_session_first_stage_from_workflow(self, workflow_dict: Dict[str, Any]) -> Optional[str]:
        """从工作流定义中获取第一个阶段ID

        Args:
            workflow_dict: 工作流定义字典

        Returns:
            第一个阶段ID或None
        """
        # 检查工作流定义是否包含stages_data
        stages_data = workflow_dict.get("stages_data")
        if not stages_data:
            # 尝试从stages字段获取
            stages_data = workflow_dict.get("stages")
            if not stages_data:
                self._log("log_warning", f"工作流 {workflow_dict.get('id')} 没有阶段数据")
                return None

        # 如果stages_data是字符串，尝试解析为JSON
        if isinstance(stages_data, str):
            try:
                stages_data = json.loads(stages_data)
            except json.JSONDecodeError:
                self._log("log_error", f"无法解析工作流 {workflow_dict.get('id')} 的阶段数据")
                return None

        # 如果stages_data是字典，尝试获取stages字段
        if isinstance(stages_data, dict):
            stages = stages_data.get("stages", [])
        else:
            # 否则假设stages_data本身就是阶段列表
            stages = stages_data

        # 确保stages是列表
        if not isinstance(stages, list):
            self._log("log_error", f"工作流 {workflow_dict.get('id')} 的阶段数据不是列表")
            return None

        # 如果没有阶段，返回None
        if not stages:
            self._log("log_warning", f"工作流 {workflow_dict.get('id')} 没有阶段")
            return None

        # 获取第一个阶段的ID
        first_stage = stages[0]
        if isinstance(first_stage, dict):
            first_stage_id = first_stage.get("id")
            if first_stage_id:
                return first_stage_id

        self._log("log_warning", f"无法从工作流 {workflow_dict.get('id')} 获取第一个阶段ID")
        return None

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
            session_name: 会话名称（可选）
            task_id: 关联的任务ID（可选）
            name: 会话名称（可选，兼容旧接口）
            flow_type: 工作流类型（可选）

        Returns:
            新创建的会话对象

        Raises:
            ValueError: 如果工作流不存在或创建失败
        """
        # Step 1: Get workflow definition
        workflow_dict = self._get_workflow_definition(workflow_id)
        if not workflow_dict:
            raise ValueError(f"找不到工作流定义 (ID: {workflow_id})")

        actual_workflow_id = workflow_dict.get("id")
        workflow_name = workflow_dict.get("name", "未命名工作流")

        self._log("log_info", f"已找到工作流: {workflow_name} (ID: {actual_workflow_id})")

        # Step 2: Determine effective task ID
        effective_task_id = task_id

        # If no task_id provided, try to get current task
        if not effective_task_id:
            try:
                from src.services.task import TaskService

                task_service = TaskService()
                current_task = task_service.get_current_task(self.session)
                if current_task:
                    effective_task_id = current_task["id"]
                    self._log("log_info", f"使用当前任务: {effective_task_id}")
            except Exception as e:
                self._log("log_warning", f"获取当前任务失败: {e}")

        # Require task_id (either provided or current)
        if not effective_task_id:
            raise ValueError("需要提供任务ID (使用 -t 参数) 或先设置当前任务 (使用 vc task update <task_id> --current)")

        # Step 3: Validate the effective_task_id
        task = self.task_repo.get_by_id(self.session, effective_task_id)
        if not task:
            logger.error(f"创建会话失败：找不到关联的任务 (ID: {effective_task_id})")
            raise ValueError(f"无法创建会话，因为找不到关联的任务 (ID: {effective_task_id})")
        else:
            logger.debug(f"验证通过：找到关联任务 {effective_task_id} (标题: {task.title})")

        # Step 4: Prepare context and create session
        # --- Name handling with uniqueness check ---
        base_name = session_name or name or f"{workflow_name}-会话"
        final_name = base_name
        counter = 1
        while self.session_repo.exists_with_name(self.session, final_name):
            logger.warning(f"会话名称 '{final_name}' 已存在，尝试添加后缀。")
            final_name = f"{base_name} - {counter}"
            counter += 1
            if counter > 100:  # Limit attempts
                raise ValueError(f"尝试为会话名称 '{base_name}' 生成唯一后缀失败")
        if final_name != base_name:
            logger.info(f"会话名称已从 '{base_name}' 重命名为 '{final_name}' 以确保唯一性。")
        # --- End Name handling ---

        context = {}
        if effective_task_id:
            context["task_id"] = effective_task_id

        try:
            # 获取工作流的第一个阶段作为起始阶段
            start_stage_id = self.get_session_first_stage_from_workflow(workflow_dict)
            self._log("log_info", f"工作流 {actual_workflow_id} 的起始阶段ID: {start_stage_id}")

            # 创建会话，并设置当前阶段ID
            new_session = self.session_repo.create_session(
                session=self.session,
                workflow_id=actual_workflow_id,
                name=final_name,  # 使用最终确定的唯一名称
                task_id=effective_task_id,
                flow_type=flow_type or workflow_dict.get("type"),
                context=context,
            )

            # 如果找到了起始阶段，设置为当前阶段
            if start_stage_id:
                self._log("log_info", f"设置会话 {new_session.id} 的当前阶段为 {start_stage_id}")
                self.session_repo.update_current_stage(self.session, new_session.id, start_stage_id)

            # 设置为当前会话
            self._set_current_session(new_session.id)

            # Step 5: Update task status
            try:
                task_service = TaskService()
                task_service.set_current_task(self.session, effective_task_id)
                task_service.update_task(self.session, effective_task_id, {"current_session_id": new_session.id})
            except Exception as e:
                self._log("log_session_error", f"设置任务关联失败 (任务ID: {effective_task_id}): {e}")

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
        return self.session_repo.find_session_by_id_or_name(self.session, id_or_name)

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
