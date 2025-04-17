"""
内存管理系统

提供内容同步、实体管理和知识存储功能。
"""

from src.memory.services import MemoryService

# 全局单例实例
_memory_service_instance = None


def get_memory_service() -> MemoryService:
    """
    获取MemoryService的单例实例

    确保全局只有一个MemoryService实例，避免重复初始化和资源浪费。

    Returns:
        MemoryService: MemoryService的单例实例
    """
    global _memory_service_instance

    if _memory_service_instance is None:
        _memory_service_instance = MemoryService()

    return _memory_service_instance


__all__ = ["MemoryService", "get_memory_service"]
