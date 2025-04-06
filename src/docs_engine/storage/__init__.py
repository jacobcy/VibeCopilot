"""
文档存储模块

提供文档存储与检索的功能
"""

# 导出错误类
from .base import StorageError
from .block_ops import BlockOperations

# 导出操作类
from .document_ops import DocumentOperations

# 导出存储引擎主类
from .engine import StorageEngine
from .link_ops import LinkOperations

# 便捷导出，使导入更简单
__all__ = [
    "StorageEngine",
    "StorageError",
    "DocumentOperations",
    "BlockOperations",
    "LinkOperations",
]
