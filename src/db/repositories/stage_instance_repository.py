"""
Stage Instance Repository Module
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import StageInstance


class StageInstanceRepository(Repository[StageInstance]):
    """阶段实例仓库"""

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, StageInstance)

    def get_by_session_id(self, session_id: str) -> List[StageInstance]:
        """根据会话ID获取阶段实例列表

        Args:
            session_id: 会话ID

        Returns:
            阶段实例列表
        """
        return (
            self.session.query(StageInstance)
            .filter(StageInstance.session_id == session_id)
            .order_by(StageInstance.created_at)  # Usually good to have an order
            .all()
        )

    def get_by_session_and_stage(self, session_id: str, stage_id: str) -> Optional[StageInstance]:
        """根据会话ID和阶段ID获取阶段实例

        Args:
            session_id: 会话ID
            stage_id: 阶段ID

        Returns:
            阶段实例对象或None
        """
        # Assuming stage_id corresponds to StageInstance.stage_name or similar identifier
        # Adjust filter if stage_id refers to a different field
        return (
            self.session.query(StageInstance)
            .filter(
                and_(
                    StageInstance.session_id == session_id,
                    StageInstance.stage_name == stage_id,  # Assuming stage_id matches stage_name
                )
            )
            .order_by(StageInstance.created_at.desc())  # Get the latest if multiple exist?
            .first()
        )

    # This method was missing in the previous read, adding based on outline
    def find_by_session_and_stage_id(self, session_id: str, stage_id_or_name: str) -> Optional[StageInstance]:
        """根据会话ID和阶段标识符（ID或名称）查找最新的阶段实例

        Args:
            session_id: 会话ID
            stage_id_or_name: 阶段的ID或名称

        Returns:
            最新的阶段实例对象或None
        """
        # It's safer to query by a unique stage ID if available on the instance
        # If stage_id_or_name is the *definition* stage ID/name, query by that.
        # Let's assume it refers to the stage identifier stored on the instance (e.g., stage_name)
        return (
            self.session.query(StageInstance)
            .filter(
                and_(
                    StageInstance.session_id == session_id,
                    StageInstance.stage_name == stage_id_or_name,  # Adjust field if necessary
                )
            )
            .order_by(StageInstance.created_at.desc())  # Get the most recent instance for that stage
            .first()
        )

    def get_by_status(self, status: str) -> List[StageInstance]:
        """根据状态获取阶段实例列表

        Args:
            status: 阶段实例状态

        Returns:
            阶段实例列表
        """
        return self.session.query(StageInstance).filter(StageInstance.status == status).order_by(StageInstance.created_at).all()

    def get_by_session_and_status(self, session_id: str, status: str) -> List[StageInstance]:
        """根据会话ID和状态获取阶段实例列表

        Args:
            session_id: 会话ID
            status: 阶段实例状态

        Returns:
            阶段实例列表
        """
        return (
            self.session.query(StageInstance)
            .filter(and_(StageInstance.session_id == session_id, StageInstance.status == status))
            .order_by(StageInstance.created_at)
            .all()
        )

    def update_status(self, instance_id: str, status: str) -> Optional[StageInstance]:
        """更新阶段实例状态

        Args:
            instance_id: 实例ID
            status: 新状态

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(instance_id)
        if not instance:
            return None

        instance.status = status
        instance.updated_at = datetime.utcnow()
        self.session.commit()
        return instance

    def add_completed_item(self, instance_id: str, item_id: str) -> Optional[StageInstance]:
        """添加已完成项

        Args:
            instance_id: 实例ID
            item_id: 已完成项ID

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(instance_id)
        if not instance:
            return None

        if not instance.completed_items:  # Assuming JSON or similar list field
            instance.completed_items = []

        # Avoid duplicates if necessary
        if item_id not in instance.completed_items:
            # Need to handle mutable JSON field correctly for SQLAlchemy
            new_list = list(instance.completed_items)
            new_list.append(item_id)
            instance.completed_items = new_list

            instance.updated_at = datetime.utcnow()
            self.session.commit()

        return instance

    def update_context(self, instance_id: str, context: Dict[str, Any]) -> Optional[StageInstance]:
        """更新阶段实例上下文

        Args:
            instance_id: 实例ID
            context: 上下文数据

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(instance_id)
        if not instance:
            return None

        if not instance.context:  # Assuming JSON field
            instance.context = {}

        # Handle mutable JSON field
        new_context = dict(instance.context)
        new_context.update(context)
        instance.context = new_context

        instance.updated_at = datetime.utcnow()
        self.session.commit()
        return instance

    def update_deliverables(self, instance_id: str, deliverables: Dict[str, Any]) -> Optional[StageInstance]:
        """更新阶段实例交付物

        Args:
            instance_id: 实例ID
            deliverables: 交付物数据

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(instance_id)
        if not instance:
            return None

        if not instance.deliverables:  # Assuming JSON field
            instance.deliverables = {}

        # Handle mutable JSON field
        new_deliverables = dict(instance.deliverables)
        new_deliverables.update(deliverables)
        instance.deliverables = new_deliverables

        instance.updated_at = datetime.utcnow()
        self.session.commit()
        return instance

    def complete_instance(self, instance_id: str, deliverables: Optional[Dict[str, Any]] = None) -> Optional[StageInstance]:
        """完成阶段实例，更新状态和结束时间，可选更新交付物

        Args:
            instance_id: 实例ID
            deliverables: 可选的最终交付物

        Returns:
            更新后的阶段实例对象或None
        """
        instance = self.get_by_id(instance_id)
        if not instance:
            return None

        now = datetime.utcnow()
        instance.status = "COMPLETED"
        instance.ended_at = now
        instance.updated_at = now

        if deliverables:
            if not instance.deliverables:
                instance.deliverables = {}
            new_deliverables = dict(instance.deliverables)
            new_deliverables.update(deliverables)
            instance.deliverables = new_deliverables

        self.session.commit()
        return instance
