# src/models/db/task.py

"""
Task数据库模型

定义任务的数据库模型结构
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.models.db.base import Base


class Task(Base):
    """任务数据库模型，代表具体工作项"""

    __tablename__ = "tasks"

    id = Column(String(50), primary_key=True, default=lambda: f"task_{uuid.uuid4().hex[:8]}")
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="todo")  # todo, in_progress, done
    priority = Column(String(20), default="medium")  # low, medium, high
    estimated_hours = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    story_id = Column(String(50), ForeignKey("stories.id"), nullable=True)
    assignee = Column(String(100), nullable=True)
    labels = Column(JSON, nullable=True)  # 存储为 JSON 列表: ["bug", "ui"]
    created_at = Column(String(50), nullable=True)
    updated_at = Column(String(50), nullable=True)
    completed_at = Column(String(50), nullable=True)
    due_date = Column(String(50), nullable=True)  # 任务截止日期，格式为ISO日期字符串
    github_issue = Column(String, nullable=True)
    current_session_id = Column(String, nullable=True)
    is_current = Column(Boolean, default=False)
    memory_references = Column(
        JSON, nullable=True
    )  # 存储为 JSON 对象列表: [{"permalink": "memory://...", "title": "文档名", "added_at": "2023-01-01T00:00:00"}]

    # 关系
    story = relationship("Story", back_populates="tasks")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    flow_sessions = relationship("FlowSession", back_populates="task")

    def __init__(self, **kwargs):
        """初始化Task，确保ID字段不为空，并设置默认值"""
        # 确保ID字段
        if not kwargs.get("id"):
            kwargs["id"] = f"task_{uuid.uuid4().hex[:8]}"

        super().__init__(**kwargs)

        # 补充默认值（在调用父类初始化后检查实例属性）
        if getattr(self, "status", None) is None:
            self.status = "todo"
        if getattr(self, "priority", None) is None:
            self.priority = "medium"
        if getattr(self, "estimated_hours", None) is None:
            self.estimated_hours = 0
        if getattr(self, "is_completed", None) is None:
            self.is_completed = False
        if getattr(self, "memory_references", None) is None:
            self.memory_references = []

        if getattr(self, "created_at", None) is None:
            self.created_at = datetime.now().isoformat()
        if getattr(self, "updated_at", None) is None:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "estimated_hours": self.estimated_hours,
            "is_completed": self.is_completed,
            "story_id": self.story_id,
            "assignee": self.assignee,
            "labels": self.labels,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "due_date": self.due_date,
            "github_issue": self.github_issue,
            "current_session_id": self.current_session_id,
            "is_current": self.is_current,
            "memory_references": self.memory_references,
        }

    def __repr__(self):
        return f"<Task(id='{self.id}', title='{self.title}', status='{self.status}')>"


class TaskComment(Base):
    """任务评论数据模型"""

    __tablename__ = "task_comments"

    id = Column(String(50), primary_key=True, default=lambda: f"comment_{uuid.uuid4().hex[:8]}")
    task_id = Column(String(50), ForeignKey("tasks.id"), nullable=False)
    author = Column(String(100), nullable=True)  # 可以是用户名或系统标识
    content = Column(Text, nullable=False)
    created_at = Column(String(50), nullable=True)

    # 关系
    task = relationship("Task", back_populates="comments")

    def __init__(self, **kwargs):
        """初始化TaskComment，确保ID字段不为空"""
        # 确保ID字段
        if not kwargs.get("id"):
            kwargs["id"] = f"comment_{uuid.uuid4().hex[:8]}"

        # 确保时间戳
        if not kwargs.get("created_at"):
            kwargs["created_at"] = datetime.now().isoformat()

        super().__init__(**kwargs)

    def to_dict(self):
        """转换为字典"""
        return {"id": self.id, "task_id": self.task_id, "author": self.author, "content": self.content, "created_at": self.created_at}
