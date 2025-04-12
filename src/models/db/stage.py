"""
工作流阶段数据模型模块

定义工作流阶段相关的数据模型，包括Stage实体。
"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class Stage(Base):
    """工作流阶段数据库模型，表示工作流中的一个阶段"""

    __tablename__ = "stages"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)
    checklist = Column(JSON, nullable=True)  # 阶段检查项列表
    deliverables = Column(JSON, nullable=True)  # 阶段交付物定义
    weight = Column(Integer, default=100)  # 阶段权重，用于排序
    estimated_time = Column(String, nullable=True)  # 预计完成时间
    is_end = Column(Boolean, default=False)  # 是否为结束阶段
    depends_on = Column(JSON, default=list)  # 依赖的阶段ID列表
    prerequisites = Column(JSON, nullable=True)  # 阶段前置条件
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    workflow = relationship("Workflow", back_populates="stages")
    instances = relationship("StageInstance", back_populates="stage")
    from_transitions = relationship("Transition", foreign_keys="[Transition.from_stage]", back_populates="from_stage_rel")
    to_transitions = relationship("Transition", foreign_keys="[Transition.to_stage]", back_populates="to_stage_rel")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "order_index": self.order_index,
            "checklist": self.checklist,
            "deliverables": self.deliverables,
            "weight": self.weight,
            "estimated_time": self.estimated_time,
            "is_end": self.is_end,
            "depends_on": self.depends_on,
            "prerequisites": self.prerequisites,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
