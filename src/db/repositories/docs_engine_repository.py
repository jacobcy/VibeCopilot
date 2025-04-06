"""
文档系统数据访问对象

提供文档、块、链接等实体的数据库访问方法
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db.docs_engine import Block, BlockType, Document, DocumentStatus, Link


class LinkType(Enum):
    """链接类型"""

    DIRECT = "direct"  # 直接链接
    REFERENCE = "reference"  # 引用链接
    BACKLINK = "backlink"  # 反向链接


class DocumentRepository(Repository[Document]):
    """文档仓库"""

    def __init__(self, session: Session):
        super().__init__(session, Document)

    def create(self, **kwargs) -> Document:
        """创建文档"""
        data = {}

        # 处理所有参数
        for key, value in kwargs.items():
            if key == "metadata":
                data["doc_metadata"] = value
            else:
                data[key] = value

        # 设置默认状态
        if "status" not in data:
            data["status"] = DocumentStatus.DRAFT

        return super().create(data)

    def find_by_path(self, path: str) -> Optional[Document]:
        """通过路径查找文档

        Args:
            path: 文档路径

        Returns:
            文档对象，如果不存在则返回None
        """
        return self.session.query(Document).filter(Document.path == path).first()

    def find_by_title(self, title: str) -> List[Document]:
        """通过标题查找文档，支持模糊匹配

        Args:
            title: 文档标题

        Returns:
            匹配的文档列表
        """
        return self.session.query(Document).filter(Document.title.like(f"%{title}%")).all()

    def find_recent(self, limit: int = 10) -> List[Document]:
        """查找最近更新的文档

        Args:
            limit: 返回数量限制

        Returns:
            最近更新的文档列表
        """
        return self.session.query(Document).order_by(Document.updated_at.desc()).limit(limit).all()

    def update_status(self, document_id: str, status: DocumentStatus) -> bool:
        """更新文档状态

        Args:
            document_id: 文档ID
            status: 新状态

        Returns:
            是否更新成功
        """
        document = self.find_by_id(document_id)
        if not document:
            return False

        document.status = status
        self.session.commit()
        return True

    def find_all_in_folder(self, folder_path: str) -> List[Document]:
        """查找指定文件夹中的所有文档

        Args:
            folder_path: 文件夹路径，例如 "/docs/"

        Returns:
            文档列表
        """
        # 确保文件夹路径以/结尾
        if not folder_path.endswith("/"):
            folder_path += "/"

        return self.session.query(Document).filter(Document.path.like(f"{folder_path}%")).all()


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


class LinkRepository(Repository[Link]):
    """链接仓库"""

    def __init__(self, session: Session):
        super().__init__(session, Link)

    def create(self, **kwargs) -> Link:
        """创建链接"""
        data = {}

        # 处理所有参数
        for key, value in kwargs.items():
            data[key] = value

        return super().create(data)

    def find_link(
        self,
        source_doc_id: str,
        target_doc_id: str,
        source_block_id: Optional[str] = None,
        target_block_id: Optional[str] = None,
    ) -> Optional[Link]:
        """查找特定链接

        Args:
            source_doc_id: 源文档ID
            target_doc_id: 目标文档ID
            source_block_id: 源块ID（可选）
            target_block_id: 目标块ID（可选）

        Returns:
            链接对象，不存在返回None
        """
        query = self.session.query(Link).filter(
            Link.source_doc_id == source_doc_id, Link.target_doc_id == target_doc_id
        )

        if source_block_id is not None:
            query = query.filter(Link.source_block_id == source_block_id)
        else:
            query = query.filter(Link.source_block_id == None)

        if target_block_id is not None:
            query = query.filter(Link.target_block_id == target_block_id)
        else:
            query = query.filter(Link.target_block_id == None)

        return query.first()

    def find_by_source_id(self, source_id: str) -> List[Link]:
        """查找从指定源出发的所有链接

        Args:
            source_id: 源ID (文档ID或块ID)

        Returns:
            链接列表
        """
        return (
            self.session.query(Link)
            .filter((Link.source_document_id == source_id) | (Link.source_block_id == source_id))
            .all()
        )

    def find_by_target_id(self, target_id: str) -> List[Link]:
        """查找指向指定目标的所有链接

        Args:
            target_id: 目标ID (文档ID或块ID)

        Returns:
            链接列表
        """
        return (
            self.session.query(Link)
            .filter((Link.target_document_id == target_id) | (Link.target_block_id == target_id))
            .all()
        )

    def find_by_document_id(self, document_id: str) -> List[Link]:
        """查找与指定文档相关的所有链接（包括出发和指向）

        Args:
            document_id: 文档ID

        Returns:
            链接列表
        """
        return (
            self.session.query(Link)
            .filter(
                (Link.source_document_id == document_id) | (Link.target_document_id == document_id)
            )
            .all()
        )

    def find_by_block_id(self, block_id: str) -> List[Link]:
        """查找与指定块相关的所有链接（包括出发和指向）

        Args:
            block_id: 块ID

        Returns:
            链接列表
        """
        return (
            self.session.query(Link)
            .filter((Link.source_block_id == block_id) | (Link.target_block_id == block_id))
            .all()
        )

    def delete_by_document_id(self, document_id: str) -> int:
        """删除与指定文档相关的所有链接

        Args:
            document_id: 文档ID

        Returns:
            删除的链接数量
        """
        result = (
            self.session.query(Link)
            .filter(
                (Link.source_document_id == document_id) | (Link.target_document_id == document_id)
            )
            .delete()
        )
        self.session.commit()
        return result

    def delete_by_block_id(self, block_id: str) -> int:
        """删除与指定块相关的所有链接

        Args:
            block_id: 块ID

        Returns:
            删除的链接数量
        """
        result = (
            self.session.query(Link)
            .filter((Link.source_block_id == block_id) | (Link.target_block_id == block_id))
            .delete()
        )
        self.session.commit()
        return result
