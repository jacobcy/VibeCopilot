"""
内存管理系统

提供统一的MemoryService接口，封装内容同步、实体管理和知识存储功能。
"""

# 导出统一的MemoryService接口和实现
from src.memory.services import MemoryService, MemoryServiceImpl

# 如果需要直接访问底层管理器（不推荐），可以取消注释以下行
# from src.memory.entity_manager import EntityManager
# from src.memory.memory_manager import MemoryManager
# from src.memory.observation_manager import ObservationManager
# from src.memory.relation_manager import RelationManager
# from src.memory.sync_executor import SyncExecutor


def get_memory_service() -> MemoryService:
    """
    获取MemoryService实例

    Returns:
        MemoryService: MemoryService接口的实例
    """
    return MemoryServiceImpl()


# 导出供外部使用的方法和类
__all__ = [
    "MemoryService",
    "MemoryServiceImpl",
    "get_memory_service",
    # "EntityManager",
    # "MemoryManager",
    # "ObservationManager",
    # "RelationManager",
    # "SyncExecutor"
]
