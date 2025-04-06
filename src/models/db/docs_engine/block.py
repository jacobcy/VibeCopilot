"""
块数据模型

定义Block实体及其关联类型
"""

import json
import uuid
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.models.db.base import Base


class BlockType(str, Enum):
    """块类型枚举"""

    TEXT = "text"  # 文本块
    CODE = "code"  # 代码块
    HEADING = "heading"  # 标题块
    IMAGE = "image"  # 图片块


class Block(Base):
    """块模型

    文档的基本组成单位，支持不同类型的内容块
    """

    __tablename__ = "blocks"

    # 基本属性
    id = Column(String, primary_key=True)  # 格式: blk-{uuid4}
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    type = Column(SQLEnum(BlockType), nullable=False, default=BlockType.TEXT)
    content = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    block_metadata = Column(JSON, default=lambda: {})

    # 关系
    document = relationship("Document", back_populates="blocks")

    @classmethod
    def generate_id(cls) -> str:
        """生成新的块ID

        Returns:
            唯一块ID
        """
        return f"blk-{uuid.uuid4()}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        """从字典创建块实例

        Args:
            data: 块数据字典

        Returns:
            块实例
        """
        # 确保ID格式正确
        if "id" not in data:
            data["id"] = cls.generate_id()
        elif not data["id"].startswith("blk-"):
            data["id"] = f"blk-{data['id']}"

        # 处理元数据
        if "metadata" in data:
            if isinstance(data["metadata"], str):
                data["block_metadata"] = json.loads(data["metadata"])
            else:
                data["block_metadata"] = data["metadata"]
            del data["metadata"]

        # 创建实例
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            块数据字典
        """
        return {
            "id": self.id,
            "document_id": self.document_id,
            "type": self.type.value if self.type else None,
            "content": self.content,
            "order": self.order,
            "metadata": self.block_metadata,
        }

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            块描述
        """
        return f"<Block(id='{self.id}', type='{self.type}', document_id='{self.document_id}')>"
