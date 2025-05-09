"""
记忆项仓库模块

提供记忆项的存储和检索功能 (仅限 CRUD 和基本查询)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional  # Ensure Dict, Any are imported

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.sql import func  # Add func import

# Ensure Repository base class is correctly imported if used
# from src.db.repository import Repository
from src.models.db.memory_item import MemoryItem

# SyncStatus enum is likely service-level concept, avoid using it directly in repo if possible
# from src.status.enums import SyncStatus

logger = logging.getLogger(__name__)


# If inheriting from a base Repository<T>, keep it. Otherwise, define as a normal class.
# class MemoryItemRepository(Repository[MemoryItem]):
class MemoryItemRepository:
    """记忆项索引仓库类 (仅负责数据访问)"""

    def __init__(self):
        """初始化仓库"""
        # If using a base class: super().__init__(MemoryItem)
        self.model_class = MemoryItem

    # --- Core CRUD & Finders ---

    def find_by_id(self, session: Session, item_id: int, include_deleted: bool = False) -> Optional[MemoryItem]:
        """根据 ID 获取 MemoryItem"""
        try:
            query = session.query(self.model_class).filter(self.model_class.id == item_id)
            if not include_deleted:
                query = query.filter(self.model_class.is_deleted == False)
            return query.first()
        except Exception as e:
            logger.error(f"通过 ID ({item_id}) 获取 MemoryItem 失败: {e}")
            raise

    def find_by_permalink(self, session: Session, permalink: str, include_deleted: bool = False) -> Optional[MemoryItem]:
        """通过 Permalink 获取 MemoryItem"""
        try:
            query = session.query(self.model_class).filter(self.model_class.permalink == permalink)
            if not include_deleted:
                query = query.filter(self.model_class.is_deleted == False)
            return query.first()
        except Exception as e:
            logger.error(f"通过 Permalink ({permalink}) 获取 MemoryItem 失败: {e}")
            raise

    def create(self, session: Session, data: Dict[str, Any]) -> MemoryItem:
        """
        创建新的 MemoryItem 记录。
        期望 'data' 包含所有必需且有效的字段。
        """
        try:
            # Basic validation or default setting can stay if simple
            data.setdefault("created_at", datetime.now(timezone.utc))
            data.setdefault("updated_at", data["created_at"])
            data.setdefault("is_deleted", False)
            data.setdefault("sync_status", "PENDING")  # Default sync status
            # Ensure summary has a default if not provided, as it's likely non-nullable
            data.setdefault("summary", data.get("title", "")[:150])

            item = self.model_class(**data)
            session.add(item)
            session.flush()  # Assign ID
            logger.info(f"创建新的 MemoryItem 成功 (id={item.id}, title='{item.title}')")
            return item
        except Exception as e:
            logger.error(f"创建 MemoryItem 失败: {e}")
            raise  # Re-raise after logging

    def update(self, session: Session, item_id: int, data: Dict[str, Any]) -> Optional[MemoryItem]:
        """
        更新指定 ID 的 MemoryItem。
        期望 'data' 包含要更新的字段及其新值。
        """
        item = self.find_by_id(session, item_id, include_deleted=False)  # Only update active items
        if not item:
            logger.warning(f"更新 MemoryItem 失败: 未找到活动项 ID={item_id}")
            return None
        try:
            # Ensure updated_at is always set on update
            data["updated_at"] = datetime.now(timezone.utc)
            updated = False
            for key, value in data.items():
                if hasattr(item, key):
                    if getattr(item, key) != value:
                        setattr(item, key, value)
                        updated = True
                else:
                    logger.warning(f"尝试更新不存在的属性 {key} for {self.model_class.__name__}")

            if updated:
                logger.info(f"更新 MemoryItem (id={item_id}) 成功")
                # No commit needed here, session scope handles it
            else:
                logger.info(f"MemoryItem (id={item_id}) 无需更新")

            return item
        except Exception as e:
            logger.error(f"更新 MemoryItem (id={item_id}) 失败: {e}")
            raise  # Re-raise after logging

    def delete(self, session: Session, item_id: int, soft_delete: bool = True) -> bool:
        """删除指定 ID 的 MemoryItem"""
        item = self.find_by_id(session, item_id, include_deleted=True)  # Find even if already deleted for hard delete case
        if not item:
            logger.warning(f"删除 MemoryItem 失败: 未找到项 ID={item_id}")
            return False
        try:
            if soft_delete:
                if not item.is_deleted:
                    item.is_deleted = True
                    item.updated_at = datetime.now(timezone.utc)
                    # Sync status might need update - handled by service layer before calling delete/update
                    logger.info(f"软删除 MemoryItem (id={item_id}) 成功")
                else:
                    logger.info(f"MemoryItem (id={item_id}) 已被软删除")
            else:
                session.delete(item)
                logger.info(f"硬删除 MemoryItem (id={item_id}) 成功")
            return True
        except Exception as e:
            logger.error(f"删除 MemoryItem (id={item_id}) 失败: {e}")
            raise  # Re-raise after logging

    def undelete(self, session: Session, item_id: int) -> bool:
        """恢复软删除的 MemoryItem"""
        item = self.find_by_id(session, item_id, include_deleted=True)
        if not item:
            logger.warning(f"恢复 MemoryItem 失败: 未找到项 ID={item_id}")
            return False
        if not item.is_deleted:
            logger.info(f"MemoryItem (id={item_id}) 未被删除，无需恢复")
            return True
        try:
            item.is_deleted = False
            item.updated_at = datetime.now(timezone.utc)
            # Sync status might need update - handled by service layer before calling undelete/update
            logger.info(f"恢复 MemoryItem (id={item_id}) 成功")
            return True
        except Exception as e:
            logger.error(f"恢复 MemoryItem (id={item_id}) 失败: {e}")
            raise

    def create_or_update_item(
        self,
        session: Session,
        permalink: str,  # Find key
        data_to_update: Dict[str, Any],  # All fields to set/update
    ) -> MemoryItem:
        """
        根据 Permalink 查找 MemoryItem，如果存在则更新，否则创建。
        期望 'data_to_update' 包含创建/更新所需的所有字段 (title, folder, summary, etc.)。
        """
        # data_to_update should contain all necessary fields including permalink itself
        data_to_update["permalink"] = permalink  # Ensure permalink is in the data

        item = self.find_by_permalink(session, permalink, include_deleted=True)  # Check even deleted items

        if item:
            # If item was deleted, undelete it first by setting is_deleted=False
            if item.is_deleted:
                logger.info(f"找到已删除的 MemoryItem (id={item.id}) 通过 permalink='{permalink}'，将进行恢复并更新。")
                data_to_update["is_deleted"] = False
            else:
                logger.debug(f"找到现有 MemoryItem (id={item.id}) 通过 permalink='{permalink}'，准备更新...")
            # Update using the standard update method after finding the ID
            updated_item = self.update(session, item.id, data_to_update)
            if updated_item is None:  # Should not happen if item was found, but handle defensively
                raise RuntimeError(f"更新 MemoryItem (id={item.id}) 失败，即使它刚刚被找到。")
            return updated_item
        else:
            logger.debug(f"未找到 Permalink='{permalink}' 的 MemoryItem，创建新记录...")
            # Create using the standard create method
            # Ensure all required fields for creation are in data_to_update
            # The 'create' method already sets defaults like created_at, updated_at
            return self.create(session, data_to_update)

    # --- Query Methods ---

    def find_items(
        self,
        session: Session,
        folder: Optional[str] = None,
        tags: Optional[List[str]] = None,  # Accept list of tags
        sync_status: Optional[str] = None,
        include_deleted: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[Any] = None,  # e.g., desc(MemoryItem.updated_at)
    ) -> List[MemoryItem]:
        """
        查找 MemoryItem 列表，支持多种过滤和排序条件。
        """
        try:
            query = session.query(self.model_class)
            filters = []

            if not include_deleted:
                filters.append(self.model_class.is_deleted == False)
            if folder is not None:  # Check for None explicitly
                filters.append(self.model_class.folder == folder)
            if sync_status is not None:
                filters.append(self.model_class.sync_status == sync_status)
            if tags:
                tag_filters = [self.model_class.tags.ilike(f"%{tag}%") for tag in tags]
                if tag_filters:
                    filters.append(and_(*tag_filters))  # Require all tags

            if filters:
                query = query.filter(and_(*filters))

            # Default order if not specified
            query = query.order_by(order_by if order_by is not None else desc(self.model_class.updated_at))

            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            return query.all()
        except Exception as e:
            logger.error(f"查找 MemoryItems 失败: {e}")
            raise

    def search_summary_title_tags(self, session: Session, query_string: str, include_deleted: bool = False) -> List[MemoryItem]:
        """在 title, summary, tags 字段中搜索"""
        try:
            filters = [
                or_(
                    self.model_class.title.ilike(f"%{query_string}%"),
                    self.model_class.summary.ilike(f"%{query_string}%"),  # Search summary
                    self.model_class.tags.ilike(f"%{query_string}%"),
                )
            ]
            if not include_deleted:
                filters.append(self.model_class.is_deleted == False)

            return session.query(self.model_class).filter(and_(*filters)).order_by(desc(self.model_class.updated_at)).all()
        except Exception as e:
            logger.error(f"内容搜索失败: {e}")
            raise

    def count_items(
        self,
        session,
        folder: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_deleted: bool = False,
    ) -> int:
        """
        计算符合条件的 MemoryItem 数量。
        """
        query = session.query(func.count(MemoryItem.id))  # Use func.count for efficiency

        if not include_deleted:
            query = query.filter(MemoryItem.is_deleted == False)

        if folder:
            # Handle potential trailing/leading slashes for consistency
            clean_folder = folder.strip("/")
            if clean_folder == "":  # Root folder case?
                query = query.filter(MemoryItem.folder == "")
            else:
                # Match exact folder or subfolders
                query = query.filter((MemoryItem.folder == clean_folder) | (MemoryItem.folder.like(f"{clean_folder}/%")))

        if tags:
            # Simple tag matching (can be improved)
            # Assumes tags are stored as comma-separated string
            for tag in tags:
                query = query.filter(MemoryItem.tags.like(f"%{tag.strip()}%"))

        count = query.scalar()
        return count if count is not None else 0

    def list_folders(self, session: Session, include_deleted: bool = False) -> List[str]:
        """获取所有文件夹列表"""
        try:
            query = session.query(self.model_class.folder).distinct()
            if not include_deleted:
                query = query.filter(self.model_class.is_deleted == False)
            # Filter out None or empty strings and sort
            folders = sorted([f[0] for f in query.all() if f[0]])
            return folders
        except Exception as e:
            logger.error(f"列出文件夹失败: {e}")
            raise

    # --- Removed Methods ---
    # - create_item (replaced by create)
    # - sync_item_from_remote (moved to service layer)
    # - mark_item_synced (moved to service layer - uses update)
    # - get_unsynced_items (replaced by find_items with sync_status filter)
    # - get_db_stats, get_folder_stats, get_tag_stats (can be built by service using count/find)
    # - get_last_updated_time (can be built by service using find_items ordered by updated_at)
    # - find_by_identifier (logic moved to service)
    # - delete_note_by_identifier (logic moved to service)
    # - delete_note_by_permalink (logic moved to service - use find_by_permalink then delete)
    # - search_items (replaced by more generic find_items)
    # - get_all (replaced by find_items without filters)
