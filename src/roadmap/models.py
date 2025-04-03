"""
数据库模型定义
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# 任务标签关联表
task_label = Table(
    "task_label_association",
    Base.metadata,
    Column("task_id", String, ForeignKey("tasks.id", ondelete="CASCADE")),
    Column("label_id", String, ForeignKey("labels.id", ondelete="CASCADE")),
)


class Epic(Base):
    """Epic实体模型"""

    __tablename__ = "epics"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="in_progress")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    stories = relationship("Story", back_populates="epic", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            status=data.get("status", "in_progress"),
        )


class Story(Base):
    """Story实体模型"""

    __tablename__ = "stories"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="in_progress")
    epic_id = Column(String, ForeignKey("epics.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    epic = relationship("Epic", back_populates="stories")
    tasks = relationship("Task", back_populates="story", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "epic_id": self.epic_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            status=data.get("status", "in_progress"),
            epic_id=data.get("epic_id"),
        )


class Task(Base):
    """Task实体模型"""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="in_progress")
    story_id = Column(String, ForeignKey("stories.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    story = relationship("Story", back_populates="tasks")
    labels = relationship("Label", secondary=task_label, back_populates="tasks")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "story_id": self.story_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "labels": [label.name for label in self.labels] if self.labels else [],
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            status=data.get("status", "in_progress"),
            story_id=data.get("story_id"),
        )


class Label(Base):
    """标签实体模型"""

    __tablename__ = "labels"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    color = Column(String, default="#0366d6")
    description = Column(Text, nullable=True)

    # 关系
    tasks = relationship("Task", secondary=task_label, back_populates="labels")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            color=data.get("color", "#0366d6"),
            description=data.get("description", ""),
        )
