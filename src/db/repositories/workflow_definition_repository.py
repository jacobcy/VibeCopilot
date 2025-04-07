"""
Workflow Definition Repository Module
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import WorkflowDefinition


class WorkflowDefinitionRepository(Repository[WorkflowDefinition]):
    """工作流定义仓库"""

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, WorkflowDefinition)

    def get_by_name(self, name: str) -> Optional[WorkflowDefinition]:
        """根据名称获取工作流定义

        Args:
            name: 工作流名称

        Returns:
            工作流定义对象或None
        """
        return self.session.query(WorkflowDefinition).filter(WorkflowDefinition.name == name).first()

    def get_by_type(self, type_name: str) -> List[WorkflowDefinition]:
        """根据类型获取工作流定义列表

        Args:
            type_name: 工作流类型

        Returns:
            工作流定义对象列表
        """
        return self.session.query(WorkflowDefinition).filter(WorkflowDefinition.type == type_name).all()
