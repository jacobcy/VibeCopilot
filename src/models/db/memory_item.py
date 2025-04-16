"""
记忆项模型模块

定义了系统记忆项的数据模型
"""

from datetime import datetime
from enum import Enum, auto
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String, Text

from .base import Base


class SyncStatus(Enum):
    """同步状态枚举"""

    NOT_SYNCED = auto()  # 未同步
    SYNCED = auto()  # 已同步
    CONFLICT = auto()  # 冲突
    ERROR = auto()  # 错误


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

    # 同步相关字段
    permalink = Column(String(255), nullable=True, unique=True, index=True)
    folder = Column(String(100), nullable=True, default="Inbox")
    is_deleted = Column(Boolean, default=False, nullable=False)
    sync_status = Column(SQLEnum(SyncStatus), default=SyncStatus.NOT_SYNCED, nullable=False)
    remote_updated_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<MemoryItem(id={self.id}, title='{self.title}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "content_type": self.content_type,
            "folder": self.folder,
            "tags": self.tags,
            "source": self.source,
            "permalink": self.permalink,
            "remote_updated_at": self.remote_updated_at.isoformat() if self.remote_updated_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_deleted": self.is_deleted,
            "sync_status": self.sync_status.name,
        }

    @classmethod
    def from_note(cls, note_data):
        """从Basic Memory笔记数据创建MemoryItem

        Args:
            note_data (dict): Basic Memory的笔记数据

        Returns:
            MemoryItem: 创建的记忆项
        """
        # 提取permalink作为唯一标识
        permalink = note_data.get("permalink")

        # 解析更新时间
        updated_at_str = note_data.get("updated_at")
        remote_updated_at = None
        if updated_at_str:
            try:
                remote_updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        return cls(
            title=note_data.get("title", "Untitled"),
            content=note_data.get("content", ""),
            content_type=note_data.get("content_type", "text"),
            folder=note_data.get("folder", "Inbox"),
            tags=note_data.get("tags"),
            source=note_data.get("source"),
            permalink=permalink,
            remote_updated_at=remote_updated_at,
            sync_status=SyncStatus.SYNCED,
        )

    def to_note_data(self):
        """转换为Basic Memory笔记数据格式

        Returns:
            dict: 适用于Basic Memory的笔记数据
        """
        note_data = {
            "title": self.title,
            "content": self.content,
            "folder": self.folder,
        }

        if self.tags:
            note_data["tags"] = self.tags

        if self.permalink:
            note_data["permalink"] = self.permalink

        return note_data
