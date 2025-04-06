"""
文档数据模型

定义Document实体及其关联类型
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import relationship

from src.models.db.base import Base


class DocumentStatus(str, Enum):
    """文档状态枚举"""

    ACTIVE = "active"  # 活跃状态
    DRAFT = "draft"  # 草稿状态
    DEPRECATED = "deprecated"  # 已废弃


class Document(Base):
    """文档模型

    具有持久化ID和块级引用支持的文档实体
    """

    __tablename__ = "documents"

    # 基本属性
    id = Column(String, primary_key=True)  # 格式: doc-{uuid4}
    title = Column(String, nullable=False)
    path = Column(String, nullable=True)  # 文档路径
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    doc_metadata = Column(JSON, default=lambda: {})

    # 关系
    replaced_by = Column(String, ForeignKey("documents.id"), nullable=True)
    blocks = relationship("Block", back_populates="document", cascade="all, delete-orphan")

    # 外部链接关系 (不使用relationship，在业务层计算以避免循环依赖)

    @classmethod
    def generate_id(cls) -> str:
        """生成新的文档ID

        Returns:
            唯一文档ID
        """
        return f"doc-{uuid.uuid4()}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """从字典创建文档实例

        Args:
            data: 文档数据字典

        Returns:
            文档实例
        """
        # 确保ID格式正确
        if "id" not in data:
            data["id"] = cls.generate_id()
        elif not data["id"].startswith("doc-"):
            data["id"] = f"doc-{data['id']}"

        # 处理元数据
        if "metadata" in data:
            if isinstance(data["metadata"], str):
                data["doc_metadata"] = json.loads(data["metadata"])
            else:
                data["doc_metadata"] = data["metadata"]
            del data["metadata"]

        # 创建实例
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            文档数据字典
        """
        return {
            "id": self.id,
            "title": self.title,
            "path": self.path,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.doc_metadata,
            "replaced_by": self.replaced_by,
        }

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            文档描述
        """
        return f"<Document(id='{self.id}', title='{self.title}', status='{self.status}')>"
