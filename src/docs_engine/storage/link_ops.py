"""
链接操作模块

提供文档和块间链接的CRUD操作和查询功能
"""

from typing import Dict, List, Optional, Tuple

from src.models.db.docs_engine import Link

from .base import BaseStorageEngine, StorageError


class LinkOperations(BaseStorageEngine):
    """链接操作类

    提供链接的创建、查询和删除操作
    """

    def create_link(
        self,
        source_doc_id: str,
        target_doc_id: str,
        source_block_id: Optional[str] = None,
        target_block_id: Optional[str] = None,
        text: Optional[str] = None,
    ) -> Link:
        """创建链接

        Args:
            source_doc_id: 源文档ID
            target_doc_id: 目标文档ID
            source_block_id: 源块ID（可选）
            target_block_id: 目标块ID（可选）
            text: 链接文本（可选）

        Returns:
            创建的Link对象

        Raises:
            StorageError: 创建失败
        """
        with self.session_factory() as session:
            try:
                _, _, link_repo = self._get_repositories(session)

                # 验证文档存在
                doc_repo, _, _ = self._get_repositories(session)
                source_doc = doc_repo.get_by_id(source_doc_id)
                target_doc = doc_repo.get_by_id(target_doc_id)

                if not source_doc:
                    raise ValueError(f"源文档不存在: {source_doc_id}")
                if not target_doc:
                    raise ValueError(f"目标文档不存在: {target_doc_id}")

                # 验证块存在（如果提供了块ID）
                if source_block_id or target_block_id:
                    _, block_repo, _ = self._get_repositories(session)

                    if source_block_id:
                        source_block = block_repo.get_by_id(source_block_id)
                        if not source_block:
                            raise ValueError(f"源块不存在: {source_block_id}")
                        if source_block.document_id != source_doc_id:
                            raise ValueError(f"源块不属于源文档: {source_block_id}")

                    if target_block_id:
                        target_block = block_repo.get_by_id(target_block_id)
                        if not target_block:
                            raise ValueError(f"目标块不存在: {target_block_id}")
                        if target_block.document_id != target_doc_id:
                            raise ValueError(f"目标块不属于目标文档: {target_block_id}")

                # 创建链接
                link = link_repo.create(
                    id=Link.generate_id(),
                    source_doc_id=source_doc_id,
                    target_doc_id=target_doc_id,
                    source_block_id=source_block_id,
                    target_block_id=target_block_id,
                    text=text,
                )
                return link
            except Exception as e:
                raise StorageError(f"创建链接失败: {str(e)}")

    def delete_link(self, link_id: str) -> bool:
        """删除链接

        Args:
            link_id: 链接ID

        Returns:
            是否删除成功

        Raises:
            StorageError: 删除失败
        """
        with self.session_factory() as session:
            try:
                _, _, link_repo = self._get_repositories(session)
                return link_repo.delete(link_id)
            except Exception as e:
                raise StorageError(f"删除链接失败: {str(e)}")

    def get_outgoing_links(self, doc_id: str) -> List[Link]:
        """获取文档的出站链接

        Args:
            doc_id: 文档ID

        Returns:
            Link对象列表

        Raises:
            StorageError: 查询失败
        """
        with self.session_factory() as session:
            try:
                _, _, link_repo = self._get_repositories(session)
                return link_repo.find_outgoing_links(doc_id)
            except Exception as e:
                raise StorageError(f"获取出站链接失败: {str(e)}")

    def get_incoming_links(self, doc_id: str) -> List[Link]:
        """获取文档的入站链接

        Args:
            doc_id: 文档ID

        Returns:
            Link对象列表

        Raises:
            StorageError: 查询失败
        """
        with self.session_factory() as session:
            try:
                _, _, link_repo = self._get_repositories(session)
                return link_repo.find_incoming_links(doc_id)
            except Exception as e:
                raise StorageError(f"获取入站链接失败: {str(e)}")

    def get_block_links(self, block_id: str) -> Tuple[List[Link], List[Link]]:
        """获取块的入站和出站链接

        Args:
            block_id: 块ID

        Returns:
            (入站链接列表, 出站链接列表)元组

        Raises:
            StorageError: 查询失败
        """
        with self.session_factory() as session:
            try:
                _, _, link_repo = self._get_repositories(session)
                incoming = link_repo.find_links_by_target_block(block_id)
                outgoing = link_repo.find_links_by_source_block(block_id)
                return incoming, outgoing
            except Exception as e:
                raise StorageError(f"获取块链接失败: {str(e)}")
