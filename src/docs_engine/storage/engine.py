"""
存储引擎模块

整合文档、块和链接操作的统一接口
"""

from typing import List, Optional, Tuple

from src.models.db.docs_engine import Block, Document, Link

from .base import BaseStorageEngine
from .block_ops import BlockOperations
from .document_ops import DocumentOperations
from .link_ops import LinkOperations


class StorageEngine(DocumentOperations, BlockOperations, LinkOperations):
    """存储引擎

    管理文档、块和链接的数据库操作，提供统一的接口
    """

    def __init__(self, session_factory=None):
        """初始化

        Args:
            session_factory: 数据库会话工厂
        """
        super().__init__(session_factory)

    def get_document_with_blocks(self, doc_id: str) -> Tuple[Optional[Document], List[Block]]:
        """获取文档及其所有块

        Args:
            doc_id: 文档ID

        Returns:
            (Document对象, Block对象列表)元组

        Raises:
            StorageError: 查询失败
        """
        document = self.get_document(doc_id)
        if not document:
            return None, []

        blocks = self.get_document_blocks(doc_id)
        return document, blocks

    def get_document_with_links(
        self, doc_id: str
    ) -> Tuple[Optional[Document], List[Link], List[Link]]:
        """获取文档及其所有链接

        Args:
            doc_id: 文档ID

        Returns:
            (Document对象, 入站链接列表, 出站链接列表)元组

        Raises:
            StorageError: 查询失败
        """
        document = self.get_document(doc_id)
        if not document:
            return None, [], []

        incoming = self.get_incoming_links(doc_id)
        outgoing = self.get_outgoing_links(doc_id)
        return document, incoming, outgoing
