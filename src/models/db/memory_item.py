"""
记忆项模型模块

定义了系统记忆项的数据模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func  # Import func for server_default

from .base import Base

# 导入 SyncStatus 枚举用于默认值，如果直接使用字符串，则不需要导入
# from src.status.enums import SyncStatus


class MemoryItem(Base):
    """记忆项模型类 - 与 Repository 和 Operations 对齐"""

    __tablename__ = "memory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    # summary = Column(Text, nullable=False)  # 内容摘要，Text类型
    summary = Column(String(1000), nullable=True)  # 改回 String(1000)，允许为空？根据仓库默认值调整
    tags = Column(String(255), nullable=True)  # 逗号分隔的标签
    permalink = Column(String(255), unique=True, nullable=False, index=True)  # 保持 unique 和 non-nullable
    folder = Column(String(255), nullable=False)  # 保持 non-nullable
    file_path = Column(String(512), nullable=True)  # 添加 file_path，允许为空?

    # 同步状态 (使用字符串)
    sync_status = Column(String(20), nullable=False, default="UNSYNCED")  # Repository create 默认是 PENDING? 统一为 UNSYNCED?

    is_deleted = Column(Boolean, nullable=False, default=False, index=True)  # 软删除标记, 添加索引
    created_at = Column(DateTime, nullable=False, server_default=func.now())  # 使用 server_default
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())  # 使用 server_default 和 onupdate

    # 移除不再使用的字段
    # content_type = Column(String(50), nullable=False, default="text")
    # source = Column(String(255), nullable=True)
    # remote_updated_at = Column(DateTime, nullable=True)
    # entity_count = Column(Integer, default=0)
    # relation_count = Column(Integer, default=0)
    # observation_count = Column(Integer, default=0)
    # vector_updated_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<MemoryItem(id={self.id}, title='{self.title}', permalink='{self.permalink}')>"
