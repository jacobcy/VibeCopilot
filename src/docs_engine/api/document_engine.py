"""
文档引擎模块

提供文档的创建、检索、更新和删除功能
"""

from typing import Any, Dict, List, Optional, Union

from src.docs_engine.storage import StorageEngine
from src.models.db.docs_engine import Document, DocumentStatus


class DocumentEngine:
    """文档引擎

    提供文档的高级操作接口
    """

    def __init__(self, storage_engine: Optional[StorageEngine] = None):
        """初始化

        Args:
            storage_engine: 存储引擎实例，如果为None则创建默认实例
        """
        self.storage = storage_engine or StorageEngine()

    def create_document(
        self,
        title: str,
        path: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """创建新文档

        Args:
            title: 文档标题
            path: 文档路径（可选）
            content: 文档内容（可选），如提供则会被分割成块
            metadata: 元数据（可选）

        Returns:
            创建的Document对象
        """
        # 1. 创建文档
        document = self.storage.create_document(
            title=title, path=path, status=DocumentStatus.DRAFT.value, metadata=metadata
        )

        # 2. 如果提供了内容，创建块
        if content and document:
            # 简单处理，将内容作为单个文本块
            self.storage.create_block(document_id=document.id, content=content, block_type="text")

        return document

    def get_document(self, doc_id: str, with_blocks: bool = False) -> Optional[Document]:
        """获取文档

        Args:
            doc_id: 文档ID
            with_blocks: 是否同时获取文档的块

        Returns:
            Document对象或None
        """
        document = self.storage.get_document(doc_id)

        if document and with_blocks:
            # 获取文档的块，通过关系已加载，无需额外操作
            pass

        return document

    def update_document(
        self,
        doc_id: str,
        title: Optional[str] = None,
        path: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Document]:
        """更新文档

        Args:
            doc_id: 文档ID
            title: 新标题（可选）
            path: 新路径（可选）
            status: 新状态（可选）
            metadata: 新元数据（可选）

        Returns:
            更新后的Document对象或None
        """
        updates = {}

        if title is not None:
            updates["title"] = title

        if path is not None:
            updates["path"] = path

        if status is not None:
            updates["status"] = status

        if metadata is not None:
            updates["metadata"] = metadata

        if not updates:
            return self.get_document(doc_id)

        return self.storage.update_document(doc_id, updates)

    def delete_document(self, doc_id: str) -> bool:
        """删除文档

        Args:
            doc_id: 文档ID

        Returns:
            是否删除成功
        """
        return self.storage.delete_document(doc_id)

    def list_documents(self, status: Optional[str] = None) -> List[Document]:
        """列出文档

        Args:
            status: 按状态过滤（可选）

        Returns:
            Document对象列表
        """
        return self.storage.list_documents(status)

    def search_documents(self, query: str) -> List[Document]:
        """搜索文档

        Args:
            query: 搜索关键词

        Returns:
            匹配的Document对象列表
        """
        return self.storage.search_documents(query)

    def deprecate_document(
        self, doc_id: str, replacement_id: Optional[str] = None
    ) -> Optional[Document]:
        """废弃文档

        Args:
            doc_id: 文档ID
            replacement_id: 替代文档ID（可选）

        Returns:
            更新后的Document对象或None
        """
        updates = {"status": DocumentStatus.DEPRECATED.value}

        if replacement_id:
            updates["replaced_by"] = replacement_id

        return self.storage.update_document(doc_id, updates)

    def publish_document(self, doc_id: str) -> Optional[Document]:
        """发布文档

        Args:
            doc_id: 文档ID

        Returns:
            更新后的Document对象或None
        """
        updates = {"status": DocumentStatus.ACTIVE.value}

        return self.storage.update_document(doc_id, updates)
