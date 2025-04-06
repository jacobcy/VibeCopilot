"""
文档操作模块

提供文档的CRUD操作和查询功能
"""

from typing import Any, Dict, List, Optional

from src.models.db.docs_engine import Document, DocumentStatus

from .base import BaseStorageEngine, StorageError


class DocumentOperations(BaseStorageEngine):
    """文档操作类

    提供文档的创建、查询、更新和删除操作
    """

    def create_document(
        self, title: str, path: str = None, status: str = "draft", metadata: Dict = None
    ) -> Document:
        """创建文档

        Args:
            title: 文档标题
            path: 文档路径
            status: 文档状态
            metadata: 元数据字典

        Returns:
            创建的Document对象

        Raises:
            StorageError: 创建失败
        """
        with self.session_factory() as session:
            try:
                doc_repo, _, _ = self._get_repositories(session)

                # 创建文档
                document = doc_repo.create(
                    id=Document.generate_id(),
                    title=title,
                    path=path,
                    status=status,
                    metadata=metadata or {},
                )
                return document
            except Exception as e:
                raise StorageError(f"创建文档失败: {str(e)}")

    def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档

        Args:
            doc_id: 文档ID

        Returns:
            Document对象或None

        Raises:
            StorageError: 查询失败
        """
        with self.session_factory() as session:
            try:
                doc_repo, _, _ = self._get_repositories(session)
                return doc_repo.get_by_id(doc_id)
            except Exception as e:
                raise StorageError(f"获取文档失败: {str(e)}")

    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> Optional[Document]:
        """更新文档

        Args:
            doc_id: 文档ID
            updates: 更新数据

        Returns:
            更新后的Document对象或None

        Raises:
            StorageError: 更新失败
        """
        with self.session_factory() as session:
            try:
                doc_repo, _, _ = self._get_repositories(session)
                return doc_repo.update(doc_id, updates)
            except Exception as e:
                raise StorageError(f"更新文档失败: {str(e)}")

    def delete_document(self, doc_id: str) -> bool:
        """删除文档

        Args:
            doc_id: 文档ID

        Returns:
            是否删除成功

        Raises:
            StorageError: 删除失败
        """
        with self.session_factory() as session:
            try:
                doc_repo, _, _ = self._get_repositories(session)
                return doc_repo.delete(doc_id)
            except Exception as e:
                raise StorageError(f"删除文档失败: {str(e)}")

    def list_documents(self, status: Optional[str] = None) -> List[Document]:
        """列出文档

        Args:
            status: 按状态过滤

        Returns:
            Document对象列表

        Raises:
            StorageError: 查询失败
        """
        with self.session_factory() as session:
            try:
                doc_repo, _, _ = self._get_repositories(session)

                if status:
                    return doc_repo.filter(status=status)
                else:
                    return doc_repo.get_all()
            except Exception as e:
                raise StorageError(f"列出文档失败: {str(e)}")

    def search_documents(self, query: str) -> List[Document]:
        """搜索文档

        Args:
            query: 搜索关键词

        Returns:
            匹配的Document对象列表

        Raises:
            StorageError: 搜索失败
        """
        with self.session_factory() as session:
            try:
                doc_repo, _, _ = self._get_repositories(session)
                return doc_repo.search(query)
            except Exception as e:
                raise StorageError(f"搜索文档失败: {str(e)}")
