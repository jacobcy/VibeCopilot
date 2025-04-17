"""
Stage Instance Repository Module
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import StageInstance
from src.utils.id_generator import EntityType, IdGenerator


class StageInstanceRepository(Repository[StageInstance]):
    """阶段实例仓库 (无状态)"""

    def __init__(self):
        """初始化 (不再存储 session)"""
        super().__init__(StageInstance)

    def create_stage_instance(
        self, session: Session, session_id: str, stage_id: str, status: str = "ACTIVE", context: Optional[Dict[str, Any]] = None
    ) -> StageInstance:
        """创建阶段实例

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID
            stage_id: 阶段ID
            status: 初始状态，默认为"ACTIVE"
            context: 上下文数据

        Returns:
            新创建的阶段实例
        """
        instance_data = {
            "id": IdGenerator.generate_stage_instance_id(),
            "session_id": session_id,
            "stage_id": stage_id,
            "status": status,
            "context": context or {},
            "deliverables": {},
            "completed_items": [],
            "started_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        new_instance = super().create(session, instance_data)
        return new_instance

    def get_all(self, session: Session) -> List[StageInstance]:
        """获取所有阶段实例

        Args:
            session: SQLAlchemy 会话对象

        Returns:
            阶段实例对象列表
        """
        return super().get_all(session, as_dict=False)

    def get_by_session_id(self, session: Session, session_id: str) -> List[StageInstance]:
        """根据会话ID获取阶段实例列表

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID

        Returns:
            阶段实例列表
        """
        return session.query(StageInstance).filter(StageInstance.session_id == session_id).order_by(StageInstance.started_at).all()

    def get_by_session_and_stage(self, session: Session, session_id: str, stage_id: str) -> Optional[StageInstance]:
        """根据会话ID和阶段ID获取阶段实例

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID
            stage_id: 阶段ID

        Returns:
            阶段实例对象或None
        """
        return (
            session.query(StageInstance)
            .filter(
                and_(
                    StageInstance.session_id == session_id,
                    StageInstance.stage_id == stage_id,
                )
            )
            .order_by(StageInstance.started_at.desc())
            .first()
        )

    def find_by_session_and_stage_id(self, session: Session, session_id: str, stage_id_or_name: str) -> Optional[StageInstance]:
        """根据会话ID和阶段标识符查找最新的阶段实例

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID
            stage_id_or_name: 阶段的ID或名称

        Returns:
            最新的阶段实例对象或None
        """
        return (
            session.query(StageInstance)
            .filter(
                and_(
                    StageInstance.session_id == session_id,
                    StageInstance.stage_id == stage_id_or_name,
                )
            )
            .order_by(StageInstance.started_at.desc())
            .first()
        )

    def get_by_status(self, session: Session, status: str) -> List[StageInstance]:
        """根据状态获取阶段实例列表

        Args:
            session: SQLAlchemy 会话对象
            status: 阶段实例状态

        Returns:
            阶段实例列表
        """
        return session.query(StageInstance).filter(StageInstance.status == status).order_by(StageInstance.started_at).all()

    def get_by_session_and_status(self, session: Session, session_id: str, status: str) -> List[StageInstance]:
        """根据会话ID和状态获取阶段实例列表

        Args:
            session: SQLAlchemy 会话对象
            session_id: 会话ID
            status: 阶段实例状态

        Returns:
            阶段实例列表
        """
        return (
            session.query(StageInstance)
            .filter(and_(StageInstance.session_id == session_id, StageInstance.status == status))
            .order_by(StageInstance.started_at)
            .all()
        )

    def update_status(self, session: Session, instance_id: str, status: str) -> Optional[StageInstance]:
        """更新阶段实例状态

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 实例ID
            status: 新状态

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(session, instance_id)
        if not instance:
            return None
        instance.status = status
        instance.updated_at = datetime.utcnow()
        return instance

    def add_completed_item(self, session: Session, instance_id: str, item_id: str) -> Optional[StageInstance]:
        """添加已完成项

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 实例ID
            item_id: 已完成项ID

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(session, instance_id)
        if not instance:
            return None
        if not instance.completed_items:
            instance.completed_items = []
        if item_id not in instance.completed_items:
            new_list = list(instance.completed_items)
            new_list.append(item_id)
            instance.completed_items = new_list
            instance.updated_at = datetime.utcnow()
        return instance

    def update_context(self, session: Session, instance_id: str, context: Dict[str, Any]) -> Optional[StageInstance]:
        """更新阶段实例上下文

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 实例ID
            context: 上下文数据

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(session, instance_id)
        if not instance:
            return None
        if not instance.context:
            instance.context = {}
        new_context = dict(instance.context)
        new_context.update(context)
        instance.context = new_context
        instance.updated_at = datetime.utcnow()
        return instance

    def update_deliverables(self, session: Session, instance_id: str, deliverables: Dict[str, Any]) -> Optional[StageInstance]:
        """更新阶段实例交付物

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 实例ID
            deliverables: 交付物数据

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(session, instance_id)
        if not instance:
            return None
        if not instance.deliverables:
            instance.deliverables = {}
        new_deliverables = dict(instance.deliverables)
        new_deliverables.update(deliverables)
        instance.deliverables = new_deliverables
        instance.updated_at = datetime.utcnow()
        return instance

    def complete_instance(self, session: Session, instance_id: str, deliverables: Optional[Dict[str, Any]] = None) -> Optional[StageInstance]:
        """完成阶段实例，包括状态更新和交付物更新

        Args:
            session: SQLAlchemy 会话对象
            instance_id: 实例ID
            deliverables: 交付物数据 (可选)

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(session, instance_id)
        if not instance:
            return None

        instance.status = "COMPLETED"
        instance.ended_at = datetime.utcnow()
        instance.updated_at = instance.ended_at

        if deliverables:
            if not instance.deliverables:
                instance.deliverables = {}
            new_deliverables = dict(instance.deliverables)
            new_deliverables.update(deliverables)
            instance.deliverables = new_deliverables

        return instance
