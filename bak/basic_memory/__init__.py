"""
基本记忆模块 - 直接转发到新的内存管理框架

此模块已被 src.memory 和 src.db.vector 替代，此文件仅做转发以保持最小兼容性。
"""

from src.db.vector.memory_adapter import BasicMemoryAdapter
from src.memory.entity_manager import EntityManager
from src.memory.observation_manager import ObservationManager
from src.memory.relation_manager import RelationManager
from src.memory.sync_service import SyncService


# 兼容类
class MemoryManager:
    """内存管理器 (兼容类)"""

    def __init__(self, config=None):
        self.entity_manager = EntityManager(config)
        self.observation_manager = ObservationManager(config)
        self.relation_manager = RelationManager(config)
        self.sync_service = SyncService()
        self.vector_store = BasicMemoryAdapter(config)

    async def sync_all(self, changed_files=None):
        """同步所有内容 (兼容方法)"""
        return await self.sync_service.sync_all(changed_files)

    async def store_entity(self, entity_type, properties, content=None):
        """存储实体 (兼容方法)"""
        return await self.entity_manager.create_entity(entity_type, properties, content)

    async def search(self, query, limit=5):
        """搜索内容 (兼容方法)"""
        return await self.vector_store.search(query, limit)


# 基类
class BaseParser:
    """基础解析器 (兼容类)"""

    pass


class BaseExporter:
    """基础导出器 (兼容类)"""

    pass


# 导出主要接口
__all__ = [
    "MemoryManager",
    "BaseParser",
    "BaseExporter",
    "EntityManager",
    "ObservationManager",
    "RelationManager",
    "SyncService",
    "BasicMemoryAdapter",
]
