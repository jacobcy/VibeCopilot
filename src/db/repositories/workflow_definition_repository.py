"""
Workflow Definition Repository Module
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, selectinload

from src.db.repository import Repository
from src.models.db import WorkflowDefinition
from src.utils.id_generator import EntityType, IdGenerator

logger = logging.getLogger(__name__)


class WorkflowDefinitionRepository(Repository[WorkflowDefinition]):
    """WorkflowDefinition仓库"""

    def __init__(self):
        """初始化"""
        super().__init__(WorkflowDefinition)

    def create_workflow(
        self,
        session: Session,
        name: str,
        workflow_type: str,
        description: Optional[str] = None,
        stages_data: Optional[List[Dict[str, Any]]] = None,
    ) -> WorkflowDefinition:
        """创建工作流定义

        Args:
            session: SQLAlchemy 会话对象
            name: 工作流名称
            workflow_type: 工作流类型
            description: 工作流描述
            stages_data: 阶段数据

        Returns:
            新创建的工作流定义
        """
        workflow_id = IdGenerator.generate_workflow_id()
        workflow_data = {
            "id": workflow_id,
            "name": name,
            "type": workflow_type,
            "description": description or "",
            "stages_data": stages_data or [],
        }
        return super().create(session, workflow_data)

    def get_by_id(self, session: Session, workflow_id: str) -> Optional[WorkflowDefinition]:
        """根据ID获取工作流定义，并预加载 transitions

        Args:
            session: SQLAlchemy 会话对象
            workflow_id: 工作流ID

        Returns:
            工作流定义对象或None
        """
        return session.query(WorkflowDefinition).options(selectinload(WorkflowDefinition.transitions)).get(workflow_id)

    def get_by_name(self, session: Session, name: str) -> Optional[WorkflowDefinition]:
        """根据名称获取工作流定义，并预加载 transitions

        Args:
            session: SQLAlchemy 会话对象
            name: 工作流名称

        Returns:
            工作流定义对象或None
        """
        return session.query(WorkflowDefinition).options(selectinload(WorkflowDefinition.transitions)).filter(WorkflowDefinition.name == name).first()

    def get_by_type(self, session: Session, type_name: str) -> List[WorkflowDefinition]:
        """根据类型获取工作流定义列表，并预加载 transitions

        Args:
            session: SQLAlchemy 会话对象
            type_name: 工作流类型

        Returns:
            工作流定义对象列表
        """
        return (
            session.query(WorkflowDefinition).options(selectinload(WorkflowDefinition.transitions)).filter(WorkflowDefinition.type == type_name).all()
        )
