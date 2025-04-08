"""
Story数据库模型

定义用户故事的数据库模型结构
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.models.db.base import Base


class Story(Base):
    """用户故事数据库模型，代表具体功能需求"""

    __tablename__ = "stories"

    id = Column(String(50), primary_key=True, default=lambda: f"story_{uuid.uuid4().hex[:8]}")
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)
    status = Column(String(50), default="backlog")
    priority = Column(String(20), default="medium")
    points = Column(Integer, default=0)
    epic_id = Column(String(50), ForeignKey("epics.id"), nullable=True)
    created_at = Column(String(50), nullable=True)
    updated_at = Column(String(50), nullable=True)

    # 关系
    epic = relationship("Epic", back_populates="stories", foreign_keys=[epic_id])
    tasks = relationship("Task", back_populates="story", foreign_keys="Task.story_id", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """初始化Story，确保ID字段不为空"""
        # 确保ID字段
        if not kwargs.get("id"):
            kwargs["id"] = f"story_{uuid.uuid4().hex[:8]}"

        # 确保时间戳
        if not kwargs.get("created_at"):
            kwargs["created_at"] = datetime.now().isoformat()
        if not kwargs.get("updated_at"):
            kwargs["updated_at"] = datetime.now().isoformat()

        super().__init__(**kwargs)

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "status": self.status,
            "priority": self.priority,
            "points": self.points,
            "epic_id": self.epic_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tasks": [task.to_dict() for task in self.tasks] if self.tasks else [],
        }
