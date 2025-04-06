"""
链接数据模型

定义Link实体及其关联操作
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from src.models.db.base import Base


class Link(Base):
    """链接模型

    记录文档间和块间的链接关系
    """

    __tablename__ = "links"

    # 基本属性
    id = Column(String, primary_key=True)  # 格式: lnk-{uuid4}
    source_doc_id = Column(String, ForeignKey("documents.id"), nullable=False)
    target_doc_id = Column(String, ForeignKey("documents.id"), nullable=False)
    source_block_id = Column(String, ForeignKey("blocks.id"), nullable=True)
    target_block_id = Column(String, ForeignKey("blocks.id"), nullable=True)
    text = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 注意：不使用relationship，避免循环依赖，通过仓库层查询

    @classmethod
    def generate_id(cls) -> str:
        """生成新的链接ID

        Returns:
            唯一链接ID
        """
        return f"lnk-{uuid.uuid4()}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Link":
        """从字典创建链接实例

        Args:
            data: 链接数据字典

        Returns:
            链接实例
        """
        # 确保ID格式正确
        if "id" not in data:
            data["id"] = cls.generate_id()
        elif not data["id"].startswith("lnk-"):
            data["id"] = f"lnk-{data['id']}"

        # 创建实例
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            链接数据字典
        """
        return {
            "id": self.id,
            "source_doc_id": self.source_doc_id,
            "target_doc_id": self.target_doc_id,
            "source_block_id": self.source_block_id,
            "target_block_id": self.target_block_id,
            "text": self.text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            链接描述
        """
        src = f"doc:{self.source_doc_id}"
        if self.source_block_id:
            src += f"/block:{self.source_block_id}"

        tgt = f"doc:{self.target_doc_id}"
        if self.target_block_id:
            tgt += f"/block:{self.target_block_id}"

        return f"<Link(id='{self.id}', {src} -> {tgt})>"
