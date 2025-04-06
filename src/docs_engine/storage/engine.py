"""
存储引擎模块

管理文档的数据库存储和访问
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from src.db import get_session_factory
from src.db.repositories.docs_engine_repository import (
    BlockRepository,
    DocumentRepository,
    LinkRepository,
)
from src.models.db.docs_engine import Block, BlockType, Document, DocumentStatus, Link


class StorageError(Exception):
    """存储操作异常"""

    pass


class StorageEngine:
    """存储引擎

    管理文档、块和链接的数据库操作
    """

    def __init__(self, session_factory=None):
        """初始化

        Args:
            session_factory: 数据库会话工厂
        """
        if session_factory is None:
            from src.db import get_engine

            engine = get_engine()
            session_factory = get_session_factory(engine)

        self.session_factory = session_factory

    def _get_repositories(
        self, session: Session
    ) -> Tuple[DocumentRepository, BlockRepository, LinkRepository]:
        """获取仓库实例

        Args:
            session: 数据库会话

        Returns:
            (文档仓库, 块仓库, 链接仓库)元组
        """
        # 创建仓库实例，注意参数顺序应为 model_class, session
        from src.models.db.docs_engine import Block, Document, Link

        doc_repo = DocumentRepository(session)
        block_repo = BlockRepository(session)
        link_repo = LinkRepository(session)
        return doc_repo, block_repo, link_repo

    # ==== 文档操作 ====

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
                # 直接使用关键字参数创建文档
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

    # ==== 块操作 ====

    def create_block(
        self,
        document_id: str,
        content: str,
        type=None,
        block_type: str = None,
        metadata: Dict = None,
        sequence: int = None,
        order: int = None,
    ) -> Block:
        """创建块

        Args:
            document_id: 文档ID
            content: 块内容
            block_type: 块类型
            metadata: 元数据字典

        Returns:
            创建的Block对象

        Raises:
            StorageError: 创建失败
        """
        with self.session_factory() as session:
            try:
                _, block_repo, _ = self._get_repositories(session)

                # 处理参数
                if block_type is not None and type is None:
                    # 兼容旧版本
                    type = block_type

                # 使用sequence或order作为块的顺序
                if sequence is not None:
                    block_order = sequence
                elif order is not None:
                    block_order = order
                else:
                    # 获取当前最大order
                    max_order = 0
                    blocks = block_repo.find_by_document_id(document_id)
                    if blocks:
                        for block in blocks:
                            if block.order > max_order:
                                max_order = block.order
                    block_order = max_order + 1

                # 创建块
                block_data = {
                    "id": Block.generate_id(),
                    "document_id": document_id,
                    "type": type,
                    "content": content,
                    "order": block_order,
                    "metadata": metadata or {},
                }

                block = block_repo.create(block_data)
                return block
            except Exception as e:
                raise StorageError(f"创建块失败: {str(e)}")

    def get_block(self, block_id: str) -> Optional[Block]:
        """获取块

        Args:
            block_id: 块ID

        Returns:
            Block对象或None

        Raises:
            StorageError: 查询失败
        """
        with self.session_factory() as session:
            try:
                _, block_repo, _ = self._get_repositories(session)
                return block_repo.get_by_id(block_id)
            except Exception as e:
                raise StorageError(f"获取块失败: {str(e)}")

    def update_block(self, block_id: str, updates: Dict[str, Any]) -> Optional[Block]:
        """更新块

        Args:
            block_id: 块ID
            updates: 更新数据

        Returns:
            更新后的Block对象或None

        Raises:
            StorageError: 更新失败
        """
        with self.session_factory() as session:
            try:
                _, block_repo, _ = self._get_repositories(session)
                return block_repo.update(block_id, updates)
            except Exception as e:
                raise StorageError(f"更新块失败: {str(e)}")

    def delete_block(self, block_id: str) -> bool:
        """删除块

        Args:
            block_id: 块ID

        Returns:
            是否删除成功

        Raises:
            StorageError: 删除失败
        """
        with self.session_factory() as session:
            try:
                _, block_repo, _ = self._get_repositories(session)
                return block_repo.delete(block_id)
            except Exception as e:
                raise StorageError(f"删除块失败: {str(e)}")

    def get_document_blocks(self, doc_id: str) -> List[Block]:
        """获取文档的所有块

        Args:
            doc_id: 文档ID

        Returns:
            Block对象列表

        Raises:
            StorageError: 查询失败
        """
        with self.session_factory() as session:
            try:
                _, block_repo, _ = self._get_repositories(session)
                return block_repo.get_by_document(doc_id)
            except Exception as e:
                raise StorageError(f"获取文档块失败: {str(e)}")

    def reorder_blocks(self, doc_id: str, block_ids: List[str]) -> bool:
        """重新排序文档的块

        Args:
            doc_id: 文档ID
            block_ids: 按新顺序排列的块ID列表

        Returns:
            是否成功

        Raises:
            StorageError: 排序失败
        """
        with self.session_factory() as session:
            try:
                _, block_repo, _ = self._get_repositories(session)
                return block_repo.reorder_blocks(doc_id, block_ids)
            except Exception as e:
                raise StorageError(f"重新排序块失败: {str(e)}")

    # ==== 链接操作 ====

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

                # 检查是否已存在相同链接
                existing = link_repo.find_link(
                    source_doc_id, target_doc_id, source_block_id, target_block_id
                )

                if existing:
                    return existing

                # 创建链接
                link_data = {
                    "id": Link.generate_id(),
                    "source_doc_id": source_doc_id,
                    "target_doc_id": target_doc_id,
                    "source_block_id": source_block_id,
                    "target_block_id": target_block_id,
                    "text": text,
                }

                link = link_repo.create(link_data)
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
        """获取文档的出链

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
                return link_repo.get_outgoing_links(doc_id)
            except Exception as e:
                raise StorageError(f"获取出链失败: {str(e)}")

    def get_incoming_links(self, doc_id: str) -> List[Link]:
        """获取文档的入链

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
                return link_repo.get_incoming_links(doc_id)
            except Exception as e:
                raise StorageError(f"获取入链失败: {str(e)}")

    def get_block_links(self, block_id: str) -> Tuple[List[Link], List[Link]]:
        """获取块的链接

        Args:
            block_id: 块ID

        Returns:
            (入链, 出链)元组

        Raises:
            StorageError: 查询失败
        """
        with self.session_factory() as session:
            try:
                _, _, link_repo = self._get_repositories(session)
                return link_repo.get_block_links(block_id)
            except Exception as e:
                raise StorageError(f"获取块链接失败: {str(e)}")
