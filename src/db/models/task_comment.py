"""
任务评论模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.db.models.base_model import BaseModel


class TaskComment(BaseModel):
    """任务评论模型类"""

    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    content = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    task = relationship("Task", back_populates="comments")

    def __repr__(self):
        return f"<TaskComment(id={self.id}, task_id={self.task_id})>"
