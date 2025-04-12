"""
记忆项模型模块

定义了系统记忆项的数据模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text

from .base import Base


class MemoryItem(Base):
    """记忆项模型类"""

    __tablename__ = "memory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False, default="text")  # text, code, image, etc.
    tags = Column(String(255), nullable=True)  # 逗号分隔的标签
    source = Column(String(255), nullable=True)  # 来源
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MemoryItem(id={self.id}, title='{self.title}')>"
