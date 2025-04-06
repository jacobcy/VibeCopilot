"""
文档存储管理模块

提供文档的存储和检索功能
"""

from .engine import StorageEngine, StorageError

__all__ = ["StorageEngine", "StorageError"]
