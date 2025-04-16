#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆项服务模块

提供对本地存储的记忆项（MemoryItem）的管理功能，包括创建、读取、更新、删除和同步。
处理与Basic Memory的同步逻辑，确保本地数据与远程数据保持一致。
此服务层通过 DatabaseService 访问 MemoryItemRepository 与数据库交互。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# 导入 DatabaseService
from src.db.service import DatabaseService
from src.models.db.memory_item import MemoryItem, SyncStatus

# 移除直接导入 MemoryItemRepository
# from src.db.repositories.memory_item_repository import MemoryItemRepository
# 移除低级数据库访问
# from ..config import get_db_path
# from ..helpers import init_db_engine, create_tables, get_session


logger = logging.getLogger(__name__)


class MemoryItemService:
    """记忆项服务类

    管理本地存储的记忆项，提供CRUD操作以及与Basic Memory的同步功能。
    通过 DatabaseService 访问 MemoryItemRepository。
    """

    def __init__(self):
        """初始化记忆项服务"""
        # 获取 DatabaseService 单例
        self.db_service = DatabaseService()

        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化记忆项服务")

    def create_item(
        self,
        title: str,
        content: str,
        folder: str = "Inbox",
        tags: Optional[str] = None,
        permalink: Optional[str] = None,
        content_type: str = "text",
        source: Optional[str] = None,
    ) -> Optional[MemoryItem]:
        """创建新的记忆项

        Args:
            title: 标题
            content: 内容
            folder: 文件夹，默认为Inbox
            tags: 标签，可选
            permalink: Basic Memory中的永久链接，可选
            content_type: 内容类型
            source: 来源

        Returns:
            Optional[MemoryItem]: 创建的记忆项，如果失败则返回None
        """
        try:
            item = self.db_service.memory_item_repo.create_item(
                title=title, content=content, folder=folder, tags=tags, permalink=permalink, content_type=content_type, source=source
            )
            return item
        except Exception as e:
            # Repository层已记录错误并回滚
            self.logger.error(f"服务层创建记忆项失败: {e}")
            return None

    def get_item_by_id(self, item_id: int, include_deleted: bool = False) -> Optional[MemoryItem]:
        """通过ID获取记忆项

        Args:
            item_id: 记忆项ID
            include_deleted: 是否包含已删除项

        Returns:
            Optional[MemoryItem]: 找到的记忆项，如果不存在则返回None
        """
        try:
            return self.db_service.memory_item_repo.get_by_id(item_id, include_deleted=include_deleted)
        except Exception as e:
            self.logger.error(f"服务层获取记忆项失败 (ID={item_id}): {e}")
            return None

    def get_item_by_permalink(self, permalink: str, include_deleted: bool = False) -> Optional[MemoryItem]:
        """通过永久链接获取记忆项

        Args:
            permalink: Basic Memory中的永久链接
            include_deleted: 是否包含已删除项

        Returns:
            Optional[MemoryItem]: 找到的记忆项，如果不存在则返回None
        """
        try:
            return self.db_service.memory_item_repo.get_by_permalink(permalink, include_deleted=include_deleted)
        except Exception as e:
            self.logger.error(f"服务层获取记忆项失败 (permalink={permalink}): {e}")
            return None

    def get_item_by_title(self, title: str, include_deleted: bool = False) -> Optional[MemoryItem]:
        """通过标题获取记忆项

        Args:
            title: 记忆项标题
            include_deleted: 是否包含已删除项

        Returns:
            Optional[MemoryItem]: 找到的记忆项，如果不存在则返回None
        """
        try:
            return self.db_service.memory_item_repo.get_by_title(title, include_deleted=include_deleted)
        except Exception as e:
            self.logger.error(f"服务层获取记忆项失败 (title={title}): {e}")
            return None

    def update_item(self, item_id: int, **kwargs) -> Optional[MemoryItem]:
        """更新记忆项

        Args:
            item_id: 记忆项ID
            **kwargs: 要更新的字段，可包括title, content, folder, tags等

        Returns:
            Optional[MemoryItem]: 更新后的记忆项，如果不存在或失败则返回None
        """
        try:
            # 传递 sync_status=SyncStatus.NOT_SYNCED （如果未指定）
            if "sync_status" not in kwargs:
                kwargs["sync_status"] = SyncStatus.NOT_SYNCED
            return self.db_service.memory_item_repo.update_item(item_id, **kwargs)
        except Exception as e:
            # Repository层已记录错误并回滚
            self.logger.error(f"服务层更新记忆项失败 (ID={item_id}): {e}")
            return None

    def delete_item(self, item_id: int, soft_delete: bool = True) -> bool:
        """删除记忆项

        Args:
            item_id: 记忆项ID
            soft_delete: 是否使用软删除，默认为True

        Returns:
            bool: 删除是否成功
        """
        try:
            return self.db_service.memory_item_repo.delete_item(item_id, soft_delete=soft_delete)
        except Exception as e:
            # Repository层已记录错误并回滚
            self.logger.error(f"服务层删除记忆项失败 (ID={item_id}): {e}")
            return False

    def search_items(
        self, query: str = "", folder: Optional[str] = None, tags: Optional[str] = None, include_deleted: bool = False
    ) -> List[MemoryItem]:
        """搜索记忆项

        Args:
            query: 搜索关键词，会匹配标题和内容
            folder: 限定文件夹
            tags: 限定标签 (逗号分隔字符串)
            include_deleted: 是否包含已删除的记忆项

        Returns:
            List[MemoryItem]: 符合条件的记忆项列表 (失败时返回空列表)
        """
        try:
            return self.db_service.memory_item_repo.search_items(query=query, folder=folder, tags=tags, include_deleted=include_deleted)
        except Exception as e:
            self.logger.error(f"服务层搜索记忆项失败: {e}")
            return []

    def list_folders(self) -> List[str]:
        """获取所有活动记忆项的文件夹列表

        Returns:
            List[str]: 文件夹名称列表 (失败时返回空列表)
        """
        try:
            return self.db_service.memory_item_repo.list_folders()
        except Exception as e:
            self.logger.error(f"服务层获取文件夹列表失败: {e}")
            return []

    def get_item_count(self, include_deleted: bool = False) -> int:
        """获取记忆项数量

        Args:
            include_deleted: 是否包含已删除的记忆项

        Returns:
            int: 记忆项数量 (失败时返回0)
        """
        try:
            return self.db_service.memory_item_repo.get_item_count(include_deleted=include_deleted)
        except Exception as e:
            self.logger.error(f"服务层获取记忆项数量失败: {e}")
            return 0

    def sync_from_remote(self, note_data: Dict[str, Any]) -> Optional[Tuple[MemoryItem, bool]]:
        """从远程同步记忆项

        将远程笔记数据同步到本地记忆项。如果本地已存在此记忆项(通过permalink匹配)，则更新；
        如果不存在，则创建新的记忆项。

        Args:
            note_data: 远程笔记数据

        Returns:
            Optional[Tuple[MemoryItem, bool]]: 元组，包含同步后的记忆项和是否是新创建的标志；失败时返回None
        """
        try:
            return self.db_service.memory_item_repo.sync_item_from_remote(note_data)
        except Exception as e:
            self.logger.error(f"服务层同步记忆项失败: {e}")
            return None

    def mark_item_synced(self, item_id: int, permalink: Optional[str] = None, remote_updated_at: Optional[datetime] = None) -> bool:
        """标记记忆项为已同步

        Args:
            item_id: 记忆项ID
            permalink: 同步后的永久链接，如果有
            remote_updated_at: 远程更新时间，如果有

        Returns:
            bool: 是否成功
        """
        try:
            return self.db_service.memory_item_repo.mark_item_synced(item_id=item_id, permalink=permalink, remote_updated_at=remote_updated_at)
        except Exception as e:
            self.logger.error(f"服务层标记记忆项同步状态失败 (ID={item_id}): {e}")
            return False

    def get_unsynced_items(self) -> List[MemoryItem]:
        """获取所有未同步的记忆项

        Returns:
            List[MemoryItem]: 未同步的记忆项列表
        """
        try:
            return self.db_service.memory_item_repo.get_unsynced_items()
        except Exception as e:
            self.logger.error(f"服务层获取未同步记忆项失败: {e}")
            return []

    def get_db_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息

        Returns:
            Dict[str, Any]: 数据库统计信息
        """
        try:
            return self.db_service.memory_item_repo.get_db_stats()
        except Exception as e:
            self.logger.error(f"服务层获取数据库统计信息失败: {e}")
            # 返回一个最小的默认结构，避免前端出错
            return {"total_items": 0, "active_items": 0, "deleted_items": 0, "unsynced_items": 0, "folders": [], "folder_counts": {}}
