"""
Flow Session Repository Module

Provides data access functionality for FlowSession entities.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import FlowSession  # Only import FlowSession model


class FlowSessionRepository(Repository[FlowSession]):
    """工作流会话仓库"""

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, FlowSession)

    def get_active_sessions(self) -> List[FlowSession]:
        """获取所有活动中的会话

        Returns:
            活动会话列表
        """
        return self.session.query(FlowSession).filter(FlowSession.status == "ACTIVE").all()

    def get_by_status(self, status: str) -> List[FlowSession]:
        """根据状态获取会话列表

        Args:
            status: 会话状态

        Returns:
            会话列表
        """
        return self.session.query(FlowSession).filter(FlowSession.status == status).all()

    def get_by_workflow_id(self, workflow_id: str) -> List[FlowSession]:
        """根据工作流ID获取会话列表

        Args:
            workflow_id: 工作流ID

        Returns:
            会话列表
        """
        # Assuming workflow_id refers to the definition ID/name stored on the session
        # Adjust field name if necessary (e.g., FlowSession.definition_id)
        return self.session.query(FlowSession).filter(FlowSession.workflow_id == workflow_id).all()

    def get_by_workflow_and_status(self, workflow_id: str, status: str) -> List[FlowSession]:
        """根据工作流ID和状态获取会话列表

        Args:
            workflow_id: 工作流ID
            status: 会话状态

        Returns:
            会话列表
        """
        return self.session.query(FlowSession).filter(and_(FlowSession.workflow_id == workflow_id, FlowSession.status == status)).all()

    # get_with_stage_instances might be less useful now as StageInstanceRepository exists
    # Consider removing or adjusting if lazy loading isn't sufficient
    def get_with_stage_instances(self, session_id: str) -> Optional[FlowSession]:
        """获取会话及其阶段实例 (using relationship loading)

        Args:
            session_id: 会话ID

        Returns:
            会话对象或None
        """
        # This relies on the relationship defined in the FlowSession model
        return self.session.query(FlowSession).filter(FlowSession.id == session_id).first()

    def update_status(self, session_id: str, status: str) -> Optional[FlowSession]:
        """更新会话状态

        Args:
            session_id: 会话ID
            status: 新状态

        Returns:
            更新后的会话对象或None
        """
        session = self.get_by_id(session_id)
        if not session:
            return None

        session.status = status
        session.updated_at = datetime.utcnow()
        self.session.commit()
        return session

    def update_current_stage(self, session_id: str, stage_id_or_name: str) -> Optional[FlowSession]:
        """更新会话当前阶段 (by stage ID or name)

        Args:
            session_id: 会话ID
            stage_id_or_name: 阶段ID或名称

        Returns:
            更新后的会话对象或None
        """
        session = self.get_by_id(session_id)
        if not session:
            return None

        # Assuming the session model stores the current stage identifier
        # Adjust field name if necessary (e.g., current_stage_name)
        session.current_stage_id = stage_id_or_name
        session.updated_at = datetime.utcnow()
        self.session.commit()
        return session

    def add_completed_stage(self, session_id: str, stage_id_or_name: str) -> Optional[FlowSession]:
        """添加已完成阶段 (by stage ID or name)

        Args:
            session_id: 会话ID
            stage_id_or_name: 已完成阶段ID或名称

        Returns:
            更新后的会话对象或None
        """
        session = self.get_by_id(session_id)
        if not session:
            return None

        if not session.completed_stages:  # Assuming JSON list field
            session.completed_stages = []

        # Avoid duplicates
        if stage_id_or_name not in session.completed_stages:
            # Handle mutable JSON field
            new_list = list(session.completed_stages)
            new_list.append(stage_id_or_name)
            session.completed_stages = new_list

            session.updated_at = datetime.utcnow()
            self.session.commit()

        return session

    def update_context(self, session_id: str, context: Dict[str, Any]) -> Optional[FlowSession]:
        """更新会话上下文

        Args:
            session_id: 会话ID
            context: 上下文数据

        Returns:
            更新后的会话对象或None
        """
        session = self.get_by_id(session_id)
        if not session:
            return None

        if not session.context:  # Assuming JSON field
            session.context = {}

        # Handle mutable JSON field
        new_context = dict(session.context)
        new_context.update(context)
        session.context = new_context

        session.updated_at = datetime.utcnow()
        self.session.commit()
        return session
