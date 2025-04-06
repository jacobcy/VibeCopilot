"""
块操作模块

提供块的CRUD操作和查询功能
"""

from typing import Any, Dict, List, Optional

from src.models.db.docs_engine import Block, BlockType

from .base import BaseStorageEngine, StorageError


class BlockOperations(BaseStorageEngine):
    """块操作类

    提供块的创建、查询、更新和删除操作
    """

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
            type: 块类型（新参数）
            block_type: 块类型（旧参数，兼容性）
            metadata: 元数据字典
            sequence: 序列号（新参数）
            order: 顺序（旧参数，兼容性）

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
                block = block_repo.create(
                    id=Block.generate_id(),
                    document_id=document_id,
                    content=content,
                    type=type or "text",
                    metadata=metadata or {},
                    order=block_order,
                )
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
                return block_repo.find_by_document_id(doc_id)
            except Exception as e:
                raise StorageError(f"获取文档块失败: {str(e)}")

    def reorder_blocks(self, doc_id: str, block_ids: List[str]) -> bool:
        """重新排序文档块

        Args:
            doc_id: 文档ID
            block_ids: 按新顺序排列的块ID列表

        Returns:
            是否重排成功

        Raises:
            StorageError: 重排失败
        """
        with self.session_factory() as session:
            try:
                _, block_repo, _ = self._get_repositories(session)

                # 获取当前文档的所有块
                blocks = block_repo.find_by_document_id(doc_id)
                block_dict = {block.id: block for block in blocks}

                # 验证所有块ID存在且属于当前文档
                for block_id in block_ids:
                    if block_id not in block_dict:
                        raise ValueError(f"块ID无效或不属于该文档: {block_id}")

                # 更新块顺序
                for i, block_id in enumerate(block_ids):
                    block_repo.update(block_id, {"order": i})

                return True
            except Exception as e:
                session.rollback()
                raise StorageError(f"重新排序块失败: {str(e)}")
