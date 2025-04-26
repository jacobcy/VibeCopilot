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
    stages_data = Column(JSON, nullable=False)  # 可用阶段列表，JSON格式
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    sessions = relationship("FlowSession", back_populates="workflow_definition", cascade="all, delete-orphan")
    stages = relationship("Stage", back_populates="workflow_definition", cascade="all, delete-orphan")
    transitions = relationship("Transition", back_populates="workflow_definition", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "stages_data": self.stages_data,
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
            stages_data=data.get("stages_data", []),
        )
