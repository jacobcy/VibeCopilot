"""
工作流定义数据模型模块

定义工作流定义相关的数据模型，包括WorkflowDefinition实体。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class WorkflowDefinition(Base):
    """工作流定义实体模型"""

    __tablename__ = "workflow_definitions"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    roadmap_id = Column(String, nullable=True)  # 关联的路线图ID
    stages = Column(JSON, nullable=False)  # 可用阶段列表，JSON格式
    source_rule = Column(String, nullable=True)  # 来源规则文件
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    sessions = relationship("FlowSession", back_populates="workflow_definition", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "roadmap_id": self.roadmap_id,
            "stages": self.stages,
            "source_rule": self.source_rule,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            type=data.get("type"),
            description=data.get("description", ""),
            roadmap_id=data.get("roadmap_id"),
            stages=data.get("stages", []),
            source_rule=data.get("source_rule"),
        )
