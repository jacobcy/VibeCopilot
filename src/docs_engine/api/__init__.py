"""
文档系统API模块

提供文档系统的核心功能接口，包括：
1. DocumentEngine: 文档引擎，负责文档的CRUD操作
2. BlockManager: 块管理器，负责文档内块级内容的管理
3. LinkManager: 链接管理器，负责文档间链接关系的管理
"""

from .block_manager import BlockManager
from .document_engine import DocumentEngine
from .link_manager import LinkManager

__all__ = ["DocumentEngine", "BlockManager", "LinkManager"]
