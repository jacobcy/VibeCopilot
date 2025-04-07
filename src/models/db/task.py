# src/models/db/task.py

import datetime
import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.models.db.base import Base


def generate_uuid():
    """生成UUID字符串"""
    return str(uuid.uuid4())


class Task(Base):
    """任务数据模型"""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="open", nullable=False, index=True)
    assignee = Column(String, nullable=True, index=True)
    labels = Column(JSON, nullable=True)  # 存储为 JSON 列表: ["bug", "ui"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # --- 关联字段 (可选) ---
    roadmap_item_id = Column(String, ForeignKey("stories.id"), nullable=True, index=True)
    workflow_session_id = Column(String, ForeignKey("flow_sessions.id"), nullable=True, index=True)
    workflow_stage_instance_id = Column(String, ForeignKey("stage_instances.id"), nullable=True, index=True)

    # --- GitHub 关联 (仅存储标识符) ---
    github_issue_number = Column(Integer, nullable=True, index=True)
    # 存储为 JSON 列表: [{"repo": "owner/repo", "pr_number": 123}, ...]
    linked_prs = Column(JSON, nullable=True)
    # 存储为 JSON 列表: [{"repo": "owner/repo", "sha": "abcdef1"}, ...]
    linked_commits = Column(JSON, nullable=True)

    # --- 关系定义 ---
    roadmap_item = relationship("Story", back_populates="tasks")
    # workflow_session = relationship("WorkflowSession", back_populates="tasks") # 假设 WorkflowSession 中有 tasks 关系
    # workflow_stage_instance = relationship("WorkflowStageInstance", back_populates="tasks") # 假设 WorkflowStageInstance 中有 tasks 关系

    comments = relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at",
    )

    def __repr__(self):
        return f"<Task(id='{self.id}', title='{self.title}', status='{self.status}')>"

    def to_dict(self):
        """将模型对象转换为字典"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TaskComment(Base):
    """任务评论数据模型"""

    __tablename__ = "task_comments"

    id = Column(String, primary_key=True, default=generate_uuid)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    author = Column(String, nullable=True)  # 可以是用户名或系统标识
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="comments")

    def __repr__(self):
        return f"<TaskComment(id='{self.id}', task_id='{self.task_id}', author='{self.author}')>"

    def to_dict(self):
        """将模型对象转换为字典"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
