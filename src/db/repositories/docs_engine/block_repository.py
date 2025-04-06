"""
块仓库模块

提供文档块的数据库访问方法
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db.docs_engine import Block, BlockType


class BlockRepository(Repository[Block]):
    """块仓库"""

    def __init__(self, session: Session):
        super().__init__(session, Block)

    def create(self, **kwargs) -> Block:
        """创建块"""
        data = {}

        # 处理所有参数
        for key, value in kwargs.items():
            if key == "metadata":
                data["block_metadata"] = value
            elif key == "sequence":
                data["order"] = value
            else:
                data[key] = value

        return super().create(data)

    def find_by_document_id(self, document_id: str) -> List[Block]:
        """查找文档的所有块

        Args:
            document_id: 文档ID

        Returns:
            块列表
        """
        return (
            self.session.query(Block)
            .filter(Block.document_id == document_id)
            .order_by(Block.order)
            .all()
        )

    def get_by_document(self, document_id: str) -> List[Block]:
        """查找文档的所有块 (别名方法)

        Args:
            document_id: 文档ID

        Returns:
            块列表
        """
        return self.find_by_document_id(document_id)

    def find_by_type(self, document_id: str, block_type: BlockType) -> List[Block]:
        """查找指定类型的块

        Args:
            document_id: 文档ID
            block_type: 块类型

        Returns:
            块列表
        """
        return (
            self.session.query(Block)
            .filter(Block.document_id == document_id, Block.type == block_type)
            .order_by(Block.order)
            .all()
        )

    def delete_by_document_id(self, document_id: str) -> int:
        """删除文档的所有块

        Args:
            document_id: 文档ID

        Returns:
            删除的块数量
        """
        result = self.session.query(Block).filter(Block.document_id == document_id).delete()
        self.session.commit()
        return result

    def update_sequence(self, block_id: str, new_sequence: int) -> bool:
        """更新块的序列号

        Args:
            block_id: 块ID
            new_sequence: 新序列号

        Returns:
            是否更新成功
        """
        block = self.find_by_id(block_id)
        if not block:
            return False

        block.sequence = new_sequence
        self.session.commit()
        return True

    def reorder_blocks(self, document_id: str, block_order: List[str]) -> bool:
        """重新排序文档的块

        Args:
            document_id: 文档ID
            block_order: 块ID列表，按新顺序排列

        Returns:
            是否重排成功
        """
        # 获取所有块
        blocks = self.find_by_document_id(document_id)
        if not blocks or len(blocks) != len(block_order):
            return False

        # 创建ID到块的映射
        block_map = {block.id: block for block in blocks}

        # 更新序列号
        for i, block_id in enumerate(block_order):
            if block_id not in block_map:
                return False
            block_map[block_id].sequence = i

        self.session.commit()
        return True
