"""
记忆项模型模块

定义了系统记忆项的数据模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from .base import Base


class MemoryItem(Base):
    """记忆项模型类"""

    __tablename__ = "memory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    summary = Column(Text, nullable=False)  # 内容摘要，必须有值
    content_type = Column(String(50), nullable=False, default="text")  # text, code, image, etc.
    tags = Column(String(255), nullable=True)  # 逗号分隔的标签
    source = Column(String(255), nullable=True)  # 来源
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, nullable=False, default=False)  # 软删除标记

    # 同步状态 (使用字符串而不是枚举避免循环导入)
    sync_status = Column(String(20), nullable=False, default="NOT_SYNCED")  # 对应SyncStatus枚举值
    remote_updated_at = Column(DateTime, nullable=True)  # 远程更新时间

    # 向量库相关字段
    permalink = Column(String(255), nullable=True, index=True)  # 向量库中的永久链接
    folder = Column(String(100), nullable=True)  # 向量库中的存储目录
    entity_count = Column(Integer, default=0)  # 解析出的实体数量
    relation_count = Column(Integer, default=0)  # 解析出的关系数量
    observation_count = Column(Integer, default=0)  # 解析出的观察数量
    vector_updated_at = Column(DateTime, nullable=True)  # 向量库更新时间

    def __repr__(self):
        return f"<MemoryItem(id={self.id}, title='{self.title}', permalink='{self.permalink}')>"
