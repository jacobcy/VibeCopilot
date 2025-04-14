"""
Workflow Definition Repository Module
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import WorkflowDefinition
from src.utils.id_generator import EntityType, IdGenerator

logger = logging.getLogger(__name__)


class WorkflowDefinitionRepository(Repository[WorkflowDefinition]):
    """WorkflowDefinition仓库"""

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, WorkflowDefinition)

    def create_workflow(
        self,
        name: str,
        workflow_type: str,
        description: Optional[str] = None,
        stages_data: Optional[List[Dict[str, Any]]] = None,
        source_rule: Optional[str] = None,
    ) -> WorkflowDefinition:
        """创建工作流定义

        Args:
            name: 工作流名称
            workflow_type: 工作流类型
            description: 工作流描述
            stages_data: 阶段数据
            source_rule: 源规则文件

        Returns:
            新创建的工作流定义
        """
        # 使用ID生成器生成标准格式的ID
        workflow_id = IdGenerator.generate_workflow_id()

        # 准备工作流数据
        workflow_data = {
            "id": workflow_id,
            "name": name,
            "type": workflow_type,
            "description": description or "",
            "stages_data": stages_data or [],
            "source_rule": source_rule,
        }

        # 使用基类的create方法创建实例
        return super().create(workflow_data)

    def get_by_id(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """根据ID获取工作流定义

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流定义对象或None
        """
        # 从数据库获取
        return super().get_by_id(workflow_id)

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
