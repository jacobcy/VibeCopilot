"""
记忆项索引模型

作为本地存储和Basic Memory之间的索引桥接
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped

from src.db.base import Base


class MemoryItem(Base):
    """记忆项索引模型类"""

    __tablename__ = "memory_items"

    id: Mapped[int] = Column(Integer, primary_key=True)
    # 基础元数据
    title: Mapped[str] = Column(String(255), nullable=False, index=True)
    summary: Mapped[str] = Column(String(500), nullable=False)  # 内容摘要
    content_type: Mapped[str] = Column(String(50), nullable=False)

    # 分类和标签
    category: Mapped[str] = Column(String(50), nullable=False, index=True)  # 主分类
    tags: Mapped[str] = Column(String(255))  # 标签列表，逗号分隔

    # 存储位置
    storage_type: Mapped[str] = Column(String(50), nullable=False)  # 'local' 或 'basic_memory'
    storage_location: Mapped[str] = Column(String(255), nullable=False)  # 存储路径或ID

    # 关系映射
    entity_refs: Mapped[str] = Column(JSON, nullable=True)  # 关联的实体ID列表
    observation_refs: Mapped[str] = Column(JSON, nullable=True)  # 关联的观察ID列表
    relation_refs: Mapped[str] = Column(JSON, nullable=True)  # 关联的关系ID列表

    # 元数据
    source: Mapped[str] = Column(String(255))  # 来源
    metadata: Mapped[dict] = Column(JSON, nullable=True)  # 额外元数据
    embedding_vector: Mapped[str] = Column(Text, nullable=True)  # 向量表示，用于语义搜索

    # 时间戳
    created_at: Mapped[datetime] = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<MemoryItem(id={self.id}, title='{self.title}', category='{self.category}')>"

    @property
    def tag_list(self) -> List[str]:
        """获取标签列表"""
        return [tag.strip() for tag in self.tags.split(",")] if self.tags else []

    @property
    def is_local(self) -> bool:
        """是否为本地存储"""
        return self.storage_type == "local"

    @property
    def is_basic_memory(self) -> bool:
        """是否存储在Basic Memory中"""
        return self.storage_type == "basic_memory"
