"""
Roadmap数据库模型

定义项目路线图的数据库模型结构
"""

import json
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from src.models.db.base import Base


class Roadmap(Base):
    """路线图数据库模型，代表项目的整体规划"""

    __tablename__ = "roadmaps"

    id = Column(String(50), primary_key=True, default=lambda: f"roadmap_{uuid.uuid4().hex[:8]}")
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0.0")
    status = Column(String(50), default="active")
    tags = Column(Text, nullable=True)  # 存储为JSON字符串
    created_at = Column(String(50), nullable=True)
    updated_at = Column(String(50), nullable=True)

    # 关系
    epics = relationship("Epic", back_populates="roadmap", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="roadmap", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """初始化Roadmap，确保ID字段不为空"""
        # 确保ID字段
        if not kwargs.get("id"):
            kwargs["id"] = f"roadmap_{uuid.uuid4().hex[:8]}"

        # 处理标签格式
        if "tags" in kwargs and isinstance(kwargs["tags"], list):
            kwargs["tags"] = json.dumps(kwargs["tags"])

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
            "version": self.version,
            "status": self.status,
            "tags": json.loads(self.tags) if self.tags else [],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "epics": [epic.to_dict() for epic in self.epics] if self.epics else [],
            "milestones": [milestone.to_dict() for milestone in self.milestones] if self.milestones else [],
        }
