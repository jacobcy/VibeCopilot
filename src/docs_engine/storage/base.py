"""
存储引擎基础模块

提供存储引擎基类和公共异常
"""

from typing import Tuple

from sqlalchemy.orm import Session

from src.db import get_session_factory
from src.db.repositories.docs_engine_repository import BlockRepository, DocumentRepository, LinkRepository


class StorageError(Exception):
    """存储操作异常"""

    pass


class BaseStorageEngine:
    """存储引擎基类

    提供基本初始化和会话管理
    """

    def __init__(self, session_factory=None):
        """初始化

        Args:
            session_factory: 数据库会话工厂
        """
        if session_factory is None:
            from src.db import get_engine

            get_engine()  # 确保数据库引擎已初始化
            session_factory = get_session_factory()

        self.session_factory = session_factory

    def _get_repositories(self, session: Session) -> Tuple[DocumentRepository, BlockRepository, LinkRepository]:
        """获取仓库实例

        Args:
            session: 数据库会话

        Returns:
            (文档仓库, 块仓库, 链接仓库)元组
        """
        # 创建仓库实例
        doc_repo = DocumentRepository(session)
        block_repo = BlockRepository(session)
        link_repo = LinkRepository(session)
        return doc_repo, block_repo, link_repo
