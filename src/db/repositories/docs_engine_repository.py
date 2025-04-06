"""
文档引擎仓库模块 (兼容层)

此文件为兼容层，将重构后的各个类重新导出，以保持API兼容性。
新代码应直接使用 src.db.repositories.docs_engine 包。
"""

from src.db.repositories.docs_engine import (
    BlockRepository,
    DocumentRepository,
    LinkRepository,
    LinkType,
)

# 重新导出所有类以保持向后兼容性
__all__ = ["BlockRepository", "DocumentRepository", "LinkRepository", "LinkType"]
