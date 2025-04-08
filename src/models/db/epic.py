"""
Epic数据库模型

定义Epic的数据库模型结构
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.models.db.base import Base


class Epic(Base):
    """Epic数据库模型，代表一个大型开发任务"""

    __tablename__ = "epics"

    id = Column(String(50), primary_key=True, default=lambda: f"epic_{uuid.uuid4().hex[:8]}")
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft")
    priority = Column(String(20), default="medium")
    roadmap_id = Column(String(50), ForeignKey("roadmaps.id"))
    created_at = Column(String(50), nullable=True)
    updated_at = Column(String(50), nullable=True)

    # 关系
    roadmap = relationship("Roadmap", back_populates="epics")
    stories = relationship("Story", back_populates="epic", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """初始化Epic，确保ID字段不为空"""
        # 确保ID字段
        if not kwargs.get("id"):
            kwargs["id"] = f"epic_{uuid.uuid4().hex[:8]}"

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
            "status": self.status,
            "priority": self.priority,
            "roadmap_id": self.roadmap_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "stories": [story.to_dict() for story in self.stories] if self.stories else [],
        }
