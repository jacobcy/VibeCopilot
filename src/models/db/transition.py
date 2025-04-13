"""
工作流转换数据模型模块

定义工作流转换相关的数据模型，包括Transition实体。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class Transition(Base):
    """工作流转换数据库模型，表示阶段间的转换关系"""

    __tablename__ = "transitions"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflow_definitions.id", ondelete="CASCADE"))
    from_stage = Column(String, ForeignKey("stages.id", ondelete="CASCADE"))
    to_stage = Column(String, ForeignKey("stages.id", ondelete="CASCADE"))
    condition = Column(Text, nullable=True)  # 转换条件
    description = Column(Text, nullable=True)  # 转换描述
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    workflow_definition = relationship("WorkflowDefinition", back_populates="transitions")
    from_stage_rel = relationship("Stage", foreign_keys=[from_stage], back_populates="from_transitions")
    to_stage_rel = relationship("Stage", foreign_keys=[to_stage], back_populates="to_transitions")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "condition": self.condition,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
