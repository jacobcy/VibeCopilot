"""
Milestone数据库模型

定义里程碑的数据库模型结构
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, Date, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.models.db.base import Base


class Milestone(Base):
    """里程碑数据库模型，代表项目中的重要时间点"""

    __tablename__ = "milestones"

    id = Column(String(50), primary_key=True, default=lambda: f"milestone_{uuid.uuid4().hex[:8]}")
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(String(50), nullable=True)  # ISO日期格式
    status = Column(String(50), default="pending")
    roadmap_id = Column(String(50), ForeignKey("roadmaps.id"))
    created_at = Column(String(50), nullable=True)
    updated_at = Column(String(50), nullable=True)

    # 关系
    roadmap = relationship("Roadmap", back_populates="milestones")

    def __init__(self, **kwargs):
        """初始化Milestone，确保ID字段不为空"""
        # 确保ID字段
        if not kwargs.get("id"):
            kwargs["id"] = f"milestone_{uuid.uuid4().hex[:8]}"

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
            "due_date": self.due_date,
            "status": self.status,
            "roadmap_id": self.roadmap_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
