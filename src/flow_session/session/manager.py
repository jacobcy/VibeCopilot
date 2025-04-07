"""
工作流会话管理器核心类模块

提供FlowSessionManager类的核心功能定义。
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from src.db import FlowSessionRepository, StageInstanceRepository, WorkflowDefinitionRepository
from src.models.db import FlowSession, StageInstance, WorkflowDefinition


class FlowSessionManager:
    """工作流会话管理器，处理会话的CRUD操作"""

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        self.session = session
        self.workflow_repo = WorkflowDefinitionRepository(session)
        self.session_repo = FlowSessionRepository(session)
        self.stage_repo = StageInstanceRepository(session)

    def create_session(self, workflow_id: str, name: Optional[str] = None) -> FlowSession:
        """创建新的工作流会话

        Args:
            workflow_id: 工作流定义ID
            name: 会话名称，如果不指定则使用工作流名称

        Returns:
            新创建的工作流会话

        Raises:
            ValueError: 如果找不到指定ID的工作流定义
        """
        workflow = self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"找不到ID为 {workflow_id} 的工作流定义")

        # 生成会话ID
        session_id = f"session-{uuid.uuid4()}"

        # 如果未提供名称，使用工作流名称
        if not name:
            name = f"{workflow.name}会话"

        # 创建会话
        session_data = {
            "id": session_id,
            "workflow_id": workflow_id,
            "name": name,
            "status": "ACTIVE",
            "context": {},
            "completed_stages": [],
        }

        flow_session = self.session_repo.create(session_data)
        return flow_session

    def get_session(self, session_id: str) -> Optional[FlowSession]:
        """获取会话详情

        Args:
            session_id: 会话ID

        Returns:
            会话对象或None
        """
        return self.session_repo.get_by_id(session_id)

    def list_sessions(
        self, status: Optional[str] = None, workflow_id: Optional[str] = None
    ) -> List[FlowSession]:
        """列出会话，可按状态和工作流ID过滤

        Args:
            status: 会话状态
            workflow_id: 工作流ID

        Returns:
            会话列表
        """
        if status and workflow_id:
            return self.session_repo.get_by_workflow_and_status(workflow_id, status)
        elif status:
            return self.session_repo.get_by_status(status)
        elif workflow_id:
            return self.session_repo.get_by_workflow_id(workflow_id)
        else:
            return self.session_repo.get_all()

    def update_session(self, session_id: str, data: Dict[str, Any]) -> Optional[FlowSession]:
        """更新会话数据

        Args:
            session_id: 会话ID
            data: 更新数据

        Returns:
            更新后的会话对象或None
        """
        return self.session_repo.update(session_id, data)

    def delete_session(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        return self.session_repo.delete(session_id)

    def pause_session(self, session_id: str) -> Optional[FlowSession]:
        """暂停会话

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话对象或None
        """
        return self.session_repo.update_status(session_id, "PAUSED")

    def resume_session(self, session_id: str) -> Optional[FlowSession]:
        """恢复会话

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话对象或None
        """
        return self.session_repo.update_status(session_id, "ACTIVE")

    def complete_session(self, session_id: str) -> Optional[FlowSession]:
        """完成会话

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话对象或None
        """
        return self.session_repo.update_status(session_id, "COMPLETED")

    def abort_session(self, session_id: str) -> Optional[FlowSession]:
        """终止会话

        Args:
            session_id: 会话ID

        Returns:
            更新后的会话对象或None
        """
        return self.session_repo.update_status(session_id, "ABORTED")

    def update_session_context(
        self, session_id: str, context: Dict[str, Any]
    ) -> Optional[FlowSession]:
        """更新会话上下文

        Args:
            session_id: 会话ID
            context: 上下文数据

        Returns:
            更新后的会话对象或None
        """
        return self.session_repo.update_context(session_id, context)
