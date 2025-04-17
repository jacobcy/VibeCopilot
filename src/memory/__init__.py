"""
内存管理系统

提供内容同步、实体管理和知识存储功能。
"""

from typing import Optional, List, Dict, Any

from src.memory.entity_manager import EntityManager
from src.memory.memory_manager import MemoryManager
from src.memory.observation_manager import ObservationManager
from src.memory.relation_manager import RelationManager
from src.memory.sync_service import SyncService


# --- Singleton Implementation for MemoryManager ---
_memory_manager_instance: Optional[MemoryManager] = None

def get_memory_service() -> MemoryManager:
    """获取MemoryManager的单例实例"""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        # 这里可以添加 MemoryManager 初始化所需的任何配置
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance


# --- Facade Service ---
class MemoryService:
    """内存服务的门面类，提供简化的接口"""

    def __init__(self):
        # 使用单例获取底层的 MemoryManager
        self._manager = get_memory_service()

    def create_note(self, content: str, title: str, folder: str, tags: Optional[str] = None) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """创建或更新笔记"""
        # 委派给 MemoryManager
        return self._manager.create_note(content=content, title=title, folder=folder, tags=tags)

    def search_notes(self, query: str, search_type: str = 'semantic') -> List[Dict[str, Any]]:
        """搜索笔记"""
        # 委派给 MemoryManager
        return self._manager.search_notes(query=query, search_type=search_type)

    def read_note(self, identifier: str) -> Optional[Dict[str, Any]]:
        """读取笔记"""
        # 委派给 MemoryManager
        return self._manager.read_note(identifier=identifier)

    def delete_note(self, identifier: str) -> bool:
        """删除笔记"""
        # 委派给 MemoryManager
        return self._manager.delete_note(identifier=identifier)

    # 可以根据需要添加更多委派方法，例如：
    # def sync(self):
    #     return self._manager.sync()
    #
    # def add_entity(self, ...):
    #     return self._manager.add_entity(...)


__all__ = [
    "EntityManager",
    "ObservationManager",
    "RelationManager",
    "SyncService",
    "MemoryManager",      # 仍然导出底层管理器，以备不时之需
    "get_memory_service", # 导出单例获取函数
    "MemoryService",      # 导出新的门面服务
]
