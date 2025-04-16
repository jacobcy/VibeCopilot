"""
内存管理系统

提供内容同步、实体管理和知识存储功能。
"""

# 核心管理器 - 底层实现
from src.memory.entity_manager import EntityManager
from src.memory.observation_manager import ObservationManager
from src.memory.relation_manager import RelationManager
from src.memory.sync_service import SyncService as LegacySyncService

from .services.memory_service import MemoryService

# 服务层 - 命令调用应使用这些服务
from .services.note_service import NoteService
from .services.search_service import SearchService
from .services.sync_service import SyncService

__all__ = [
    # 服务层
    "NoteService",
    "SearchService",
    "SyncService",
    "MemoryService",
    # 核心管理器
    "EntityManager",
    "ObservationManager",
    "RelationManager",
    "LegacySyncService",
]
