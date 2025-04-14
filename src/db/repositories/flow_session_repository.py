"""
Flow Session Repository Module

Provides data access functionality for FlowSession entities.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import FlowSession  # Only import FlowSession model

# 创建日志记录器
logger = logging.getLogger(__name__)


class FlowSessionRepository(Repository[FlowSession]):
    """工作流会话仓库"""

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, FlowSession)

    def get_all(self) -> List[FlowSession]:
        """获取所有会话

        重写父类的get_all方法，确保返回FlowSession对象列表而非字典列表

        Returns:
            会话对象列表
        """
        logger.debug("FlowSessionRepository.get_all() 被调用")
        sessions = self.session.query(FlowSession).all()
        logger.debug(f"获取到 {len(sessions)} 个会话对象")

        for i, s in enumerate(sessions):
            logger.debug(f"会话 {i+1}: ID={s.id}, 名称={s.name}, 工作流={s.workflow_id}, 状态={s.status}")

        return sessions

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

    def get_by_name(self, name: str) -> Optional[FlowSession]:
        """根据会话名称获取会话

        Args:
            name: 会话名称

        Returns:
            会话对象或None
        """
        return self.session.query(FlowSession).filter(FlowSession.name == name).first()

    def find_session_by_id_or_name(self, id_or_name: str) -> Optional[FlowSession]:
        """根据ID或名称查找会话

        首先尝试按ID查找，如果没有找到，再按名称查找

        Args:
            id_or_name: 会话ID或名称

        Returns:
            会话对象或None
        """
        # 先尝试作为ID查找
        session = self.get_by_id(id_or_name)
        if session:
            return session

        # 如果没找到，尝试作为名称查找
        return self.get_by_name(id_or_name)

    def link_to_task(self, session_id: str, task_id: Optional[str]) -> Optional[FlowSession]:
        """关联或取消关联会话到任务

        Args:
            session_id: 会话ID
            task_id: 任务ID，None表示取消关联

        Returns:
            更新后的会话对象或None
        """
        session = self.get_by_id(session_id)
        if not session:
            return None

        session.task_id = task_id
        session.updated_at = datetime.utcnow()
        self.session.commit()
        return session

    def get_by_task_id(self, task_id: str) -> List[FlowSession]:
        """根据任务ID获取相关的所有会话

        Args:
            task_id: 任务ID

        Returns:
            会话列表
        """
        return self.session.query(FlowSession).filter(FlowSession.task_id == task_id).all()

    def set_current_session(self, session_id: str) -> bool:
        """设置当前会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功设置
        """
        try:
            # 清除其他会话的当前状态
            self.session.query(FlowSession).filter(FlowSession.is_current == True).update({"is_current": False})
            # 设置新的当前会话
            session = self.get_by_id(session_id)
            if session:
                session.is_current = True
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"设置当前会话失败: {e}")
            return False
