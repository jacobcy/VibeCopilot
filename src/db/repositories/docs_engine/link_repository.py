"""
链接仓库模块

提供文档和块之间链接的数据库访问方法
"""

from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db.docs_engine import Link


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

        查找从特定源到特定目标的链接，可以指定块级别的链接。

        Args:
            source_doc_id: 源文档ID
            target_doc_id: 目标文档ID
            source_block_id: 源块ID，如果为None则只匹配文档级别
            target_block_id: 目标块ID，如果为None则只匹配文档级别

        Returns:
            链接对象，如果不存在则返回None
        """
        query = self.session.query(Link).filter(
            Link.source_doc_id == source_doc_id, Link.target_doc_id == target_doc_id
        )

        if source_block_id is not None:
            query = query.filter(Link.source_block_id == source_block_id)
        else:
            query = query.filter(Link.source_block_id.is_(None))

        if target_block_id is not None:
            query = query.filter(Link.target_block_id == target_block_id)
        else:
            query = query.filter(Link.target_block_id.is_(None))

        return query.first()

    def find_by_source_id(self, source_id: str) -> List[Link]:
        """查找从特定源文档或块出发的所有链接

        Args:
            source_id: 源文档ID或源块ID

        Returns:
            链接列表
        """
        return (
            self.session.query(Link)
            .filter(or_(Link.source_doc_id == source_id, Link.source_block_id == source_id))
            .all()
        )

    def find_by_target_id(self, target_id: str) -> List[Link]:
        """查找指向特定目标文档或块的所有链接

        Args:
            target_id: 目标文档ID或目标块ID

        Returns:
            链接列表
        """
        return (
            self.session.query(Link)
            .filter(or_(Link.target_doc_id == target_id, Link.target_block_id == target_id))
            .all()
        )

    def find_by_document_id(self, document_id: str) -> List[Link]:
        """查找与特定文档相关的所有链接

        查找从该文档出发或指向该文档的所有链接。

        Args:
            document_id: 文档ID

        Returns:
            链接列表
        """
        return (
            self.session.query(Link)
            .filter(or_(Link.source_doc_id == document_id, Link.target_doc_id == document_id))
            .all()
        )

    def find_by_block_id(self, block_id: str) -> List[Link]:
        """查找与特定块相关的所有链接

        查找从该块出发或指向该块的所有链接。

        Args:
            block_id: 块ID

        Returns:
            链接列表
        """
        return (
            self.session.query(Link)
            .filter(or_(Link.source_block_id == block_id, Link.target_block_id == block_id))
            .all()
        )

    def delete_by_document_id(self, document_id: str) -> int:
        """删除与特定文档相关的所有链接

        Args:
            document_id: 文档ID

        Returns:
            删除的链接数量
        """
        result = (
            self.session.query(Link)
            .filter(or_(Link.source_doc_id == document_id, Link.target_doc_id == document_id))
            .delete(synchronize_session=False)
        )

        self.session.commit()
        return result

    def delete_by_block_id(self, block_id: str) -> int:
        """删除与特定块相关的所有链接

        Args:
            block_id: 块ID

        Returns:
            删除的链接数量
        """
        result = (
            self.session.query(Link)
            .filter(or_(Link.source_block_id == block_id, Link.target_block_id == block_id))
            .delete(synchronize_session=False)
        )

        self.session.commit()
        return result
