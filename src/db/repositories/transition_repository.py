"""
Transition Repository Module

提供对Transition模型的数据库操作，包括查询、创建、更新、删除等。
"""

from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import Transition
from src.utils.id_generator import EntityType, IdGenerator


class TransitionRepository(Repository[Transition]):
    """转换仓库"""

    def __init__(self):
        super().__init__(Transition)

    def create_transition(
        self,
        session: Session,
        workflow_id: str,
        from_stage: str,
        to_stage: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> Transition:
        """创建转换

        Args:
            session: SQLAlchemy 会话对象
            workflow_id: 工作流ID
            from_stage: 源阶段ID
            to_stage: 目标阶段ID
            name: 转换名称
            description: 转换描述
            condition: 转换条件

        Returns:
            Transition: 创建的转换
        """
        transition_id = IdGenerator.generate_transition_id()
        transition_data = {
            "id": transition_id,
            "workflow_id": workflow_id,
            "from_stage": from_stage,
            "to_stage": to_stage,
            "name": name or f"从{from_stage}到{to_stage}",
            "description": description or "",
            "condition": condition or "true",
        }
        return super().create(session, transition_data)

    def get_all(self, session: Session) -> List[Transition]:
        """获取所有转换

        Args:
            session: SQLAlchemy 会话对象
        Returns:
            List[Transition]: 转换列表
        """
        return session.query(self.model_class).all()

    def get_by_workflow_id(self, session: Session, workflow_id: str) -> List[Transition]:
        """根据工作流ID获取转换

        Args:
            session: SQLAlchemy 会话对象
            workflow_id: 工作流ID

        Returns:
            List[Transition]: 转换列表
        """
        return session.query(self.model_class).filter(self.model_class.workflow_id == workflow_id).all()

    def get_by_id(self, session: Session, transition_id: str) -> Optional[Transition]:
        """根据ID获取转换

        Args:
            session: SQLAlchemy 会话对象
            transition_id: 转换ID

        Returns:
            Optional[Transition]: 转换，如果不存在则返回None
        """
        return session.query(self.model_class).filter(self.model_class.id == transition_id).first()

    def get_by_from_stage(self, session: Session, stage_id: str) -> List[Transition]:
        """根据源阶段ID获取转换

        Args:
            session: SQLAlchemy 会话对象
            stage_id: 阶段ID

        Returns:
            List[Transition]: 转换列表
        """
        return session.query(self.model_class).filter(self.model_class.from_stage == stage_id).all()

    def get_by_to_stage(self, session: Session, stage_id: str) -> List[Transition]:
        """根据目标阶段ID获取转换

        Args:
            session: SQLAlchemy 会话对象
            stage_id: 阶段ID

        Returns:
            List[Transition]: 转换列表
        """
        return session.query(self.model_class).filter(self.model_class.to_stage == stage_id).all()

    def create(self, session: Session, transition_data: dict) -> Transition:
        """创建转换

        Args:
            session: SQLAlchemy 会话对象
            transition_data: 转换数据

        Returns:
            Transition: 创建的转换
        """
        transition = Transition(**transition_data)
        session.add(transition)
        return transition

    def update(self, session: Session, transition_id: str, transition_data: dict) -> Optional[Transition]:
        """更新转换

        Args:
            session: SQLAlchemy 会话对象
            transition_id: 转换ID
            transition_data: 转换数据

        Returns:
            Optional[Transition]: 更新后的转换，如果不存在则返回None
        """
        transition = self.get_by_id(session, transition_id)
        if not transition:
            return None

        for key, value in transition_data.items():
            if hasattr(transition, key):
                setattr(transition, key, value)

        return transition

    def delete(self, session: Session, transition_id: str) -> bool:
        """删除转换

        Args:
            session: SQLAlchemy 会话对象
            transition_id: 转换ID

        Returns:
            bool: 是否删除成功
        """
        transition = self.get_by_id(session, transition_id)
        if not transition:
            return False

        session.delete(transition)
        return True
