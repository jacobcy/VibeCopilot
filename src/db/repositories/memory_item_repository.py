"""
记忆项仓库模块

提供记忆项的存储和检索功能
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.memory.helpers import is_permalink, normalize_path, path_to_permalink  # 导入必要的helper
from src.models.db import MemoryItem, SyncStatus  # 导入SyncStatus

logger = logging.getLogger(__name__)


class MemoryItemRepository(Repository[MemoryItem]):
    """记忆项索引仓库类"""

    def __init__(self, session: Session):
        """初始化仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, MemoryItem)

    def create_item(
        self,
        title: str,
        content: str,
        folder: str = "Inbox",
        tags: Optional[str] = None,
        permalink: Optional[str] = None,
        content_type: str = "text",
        source: Optional[str] = None,
        sync_status: SyncStatus = SyncStatus.NOT_SYNCED,
    ) -> MemoryItem:
        """创建新的记忆项 (整合自 helpers.item_utils.create_memory_item)

        Args:
            title: 标题
            content: 内容
            folder: 文件夹，默认为Inbox
            tags: 标签（逗号分隔），可选
            permalink: Basic Memory中的永久链接，可选
            content_type: 内容类型，默认为text
            source: 来源，可选
            sync_status: 同步状态，默认未同步

        Returns:
            MemoryItem: 创建的记忆项
        """
        # 规范化文件夹路径
        folder = normalize_path(folder)

        # 如果提供了permalink，确保其格式正确
        if permalink and not is_permalink(permalink):
            permalink = path_to_permalink(permalink)

        # 使用基础 Repository 的 create 方法
        data = {
            "title": title,
            "content": content,
            "content_type": content_type,
            "folder": folder,
            "tags": tags,
            "permalink": permalink,
            "source": source,
            "sync_status": sync_status,
        }
        try:
            item = super().create(data)
            logger.info(f"创建记忆项: {item.title} (文件夹: {folder})")
            return item
        except Exception as e:
            logger.error(f"创建记忆项失败: {str(e)}")
            self.session.rollback()  # 确保回滚
            raise

    def get_by_id(self, memory_item_id: int, include_deleted: bool = False) -> Optional[MemoryItem]:
        """
        根据ID获取记忆项 (整合自 helpers.item_utils.get_item_by_id)

        Args:
            memory_item_id: 记忆项ID
            include_deleted: 是否包含已删除项

        Returns:
            Optional[MemoryItem]: 找到的记忆项，如果不存在则返回None
        """
        try:
            query = self.session.query(MemoryItem).filter(MemoryItem.id == memory_item_id)
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            return query.first()
        except Exception as e:
            logger.error(f"获取记忆项失败 (ID={memory_item_id}): {str(e)}")
            raise

    def get_by_permalink(self, permalink: str, include_deleted: bool = False) -> Optional[MemoryItem]:
        """通过永久链接获取记忆项 (来自 helpers.item_utils.get_item_by_permalink)

        Args:
            session: 数据库会话
            permalink: Basic Memory中的永久链接
            include_deleted: 是否包含已删除项

        Returns:
            Optional[MemoryItem]: 找到的记忆项，如果不存在则返回None
        """
        # 确保永久链接格式正确
        if not is_permalink(permalink):
            permalink = path_to_permalink(permalink)

        try:
            query = self.session.query(MemoryItem).filter(MemoryItem.permalink == permalink)
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            return query.first()
        except Exception as e:
            logger.error(f"获取记忆项失败 (permalink={permalink}): {str(e)}")
            raise

    def get_by_title(self, title: str, include_deleted: bool = False) -> Optional[MemoryItem]:
        """通过标题获取记忆项 (来自 helpers.sync_utils.get_item_by_title)

        Args:
            title: 记忆项标题
            include_deleted: 是否包含已删除项

        Returns:
            Optional[MemoryItem]: 找到的记忆项，如果不存在则返回None
        """
        try:
            query = self.session.query(MemoryItem).filter(MemoryItem.title == title)
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            return query.first()
        except Exception as e:
            logger.error(f"获取记忆项失败 (title={title}): {str(e)}")
            raise

    def update_item(self, memory_item_id: int, **kwargs) -> Optional[MemoryItem]:
        """
        更新记忆项 (整合自 helpers.item_utils.update_memory_item 和 repo.update)

        Args:
            memory_item_id: 记忆项ID
            **kwargs: 要更新的字段

        Returns:
            Optional[MemoryItem]: 更新后的记忆项，如果不存在则返回None
        """
        # 预处理字段
        if "folder" in kwargs:
            kwargs["folder"] = normalize_path(kwargs["folder"])

        if "permalink" in kwargs and kwargs["permalink"] and not is_permalink(kwargs["permalink"]):
            kwargs["permalink"] = path_to_permalink(kwargs["permalink"])

        try:
            # 获取未删除的项
            item = self.get_by_id(memory_item_id, include_deleted=False)

            if not item:
                logger.warning(f"更新记忆项失败: 未找到ID为{memory_item_id}的活动记忆项")
                return None

            # 如果没有显式传入 sync_status，则标记为未同步
            if "sync_status" not in kwargs:
                item.sync_status = SyncStatus.NOT_SYNCED

            # 更新字段
            updated = False
            for key, value in kwargs.items():
                if hasattr(item, key) and getattr(item, key) != value:
                    setattr(item, key, value)
                    updated = True

            # 只有在实际更新了字段时才提交
            if updated:
                self.session.commit()
                logger.info(f"更新记忆项: {item.title} (ID={memory_item_id})")
            else:
                logger.info(f"记忆项无需更新: {item.title} (ID={memory_item_id})")
            return item
        except Exception as e:
            self.session.rollback()
            logger.error(f"更新记忆项失败 (ID={memory_item_id}): {str(e)}")
            raise

    def delete_item(self, memory_item_id: int, soft_delete: bool = True) -> bool:
        """
        删除记忆项 (整合自 helpers.item_utils.delete_memory_item 和 repo.delete)

        Args:
            memory_item_id: 记忆项ID
            soft_delete: 是否使用软删除，默认为True

        Returns:
            bool: 删除是否成功
        """
        try:
            # 获取项目，无论是否已删除，以便硬删除
            item = self.get_by_id(memory_item_id, include_deleted=True)

            if not item:
                logger.warning(f"删除记忆项失败: 未找到ID为{memory_item_id}的记忆项")
                return False

            if soft_delete:
                if not item.is_deleted:  # 避免重复软删除
                    item.is_deleted = True
                    item.sync_status = SyncStatus.NOT_SYNCED  # 软删除也需要同步
                    self.session.commit()
                    logger.info(f"软删除记忆项: {item.title} (ID={memory_item_id})")
                else:
                    logger.info(f"记忆项已软删除: {item.title} (ID={memory_item_id})")
            else:
                self.session.delete(item)
                self.session.commit()
                logger.info(f"硬删除记忆项: {item.title} (ID={memory_item_id})")

            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"删除记忆项失败 (ID={memory_item_id}): {str(e)}")
            raise

    def search_items(
        self, query: str = "", folder: Optional[str] = None, tags: Optional[str] = None, include_deleted: bool = False
    ) -> List[MemoryItem]:
        """搜索记忆项 (来自 helpers.item_utils.search_memory_items)

        Args:
            query: 搜索关键词，会匹配标题和内容
            folder: 限定文件夹
            tags: 限定标签
            include_deleted: 是否包含已删除的记忆项

        Returns:
            List[MemoryItem]: 符合条件的记忆项列表
        """
        # 规范化文件夹路径
        if folder:
            folder = normalize_path(folder)

        try:
            filters = []

            # 是否包含已删除项
            if not include_deleted:
                filters.append(MemoryItem.is_deleted == False)

            # 搜索关键词
            if query:
                filters.append(or_(MemoryItem.title.ilike(f"%{query}%"), MemoryItem.content.ilike(f"%{query}%")))

            # 文件夹过滤
            if folder:
                filters.append(MemoryItem.folder == folder)

            # 标签过滤 (假设tags是逗号分隔的字符串，需要分别匹配)
            if tags:
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                tag_filters = [MemoryItem.tags.ilike(f"%{tag}%") for tag in tag_list]
                if tag_filters:
                    filters.append(and_(*tag_filters))  # 或者 or_ 取决于需求

            # 执行查询
            items_query = self.session.query(MemoryItem)
            if filters:
                items_query = items_query.filter(and_(*filters))

            # 按更新时间排序
            items = items_query.order_by(MemoryItem.updated_at.desc()).all()

            return items
        except Exception as e:
            logger.error(f"搜索记忆项失败: {str(e)}")
            raise

    def sync_item_from_remote(self, note_data: Dict[str, Any]) -> Tuple[MemoryItem, bool]:
        """从远程笔记数据同步记忆项 (来自 helpers.sync_utils.sync_item_from_remote)

        如果本地存在对应记忆项则更新，否则创建新记忆项

        Args:
            note_data: Basic Memory笔记数据

        Returns:
            Tuple[MemoryItem, bool]: 同步后的记忆项和是否是新创建的标志
        """
        permalink = note_data.get("permalink")
        if not permalink:
            raise ValueError("同步记忆项失败: 远程笔记数据缺少permalink")

        # 确保permalink格式正确
        if not is_permalink(permalink):
            permalink = path_to_permalink(permalink)
            # note_data["permalink"] = permalink # 不应修改输入字典

        # 处理文件夹路径
        folder = normalize_path(note_data.get("folder", "Inbox"))

        try:
            # 查找本地是否存在
            item = self.get_by_permalink(permalink, include_deleted=True)  # 包含已删除项，以便恢复

            is_new = False
            # 不存在则创建
            if not item:
                item = self.create_item(
                    title=note_data.get("title", "Untitled"),
                    content=note_data.get("content", ""),
                    content_type=note_data.get("content_type", "text"),
                    folder=folder,
                    tags=note_data.get("tags"),
                    source=note_data.get("source"),
                    permalink=permalink,
                    sync_status=SyncStatus.SYNCED,  # 从远程同步过来的，初始状态就是 SYNCED
                )
                is_new = True
                logger.info(f"从远程创建记忆项: {item.title}")
            else:
                # 检查是否需要更新
                remote_updated_at_str = note_data.get("updated_at")
                remote_updated_at = None
                if remote_updated_at_str:
                    try:
                        remote_updated_at = datetime.fromisoformat(remote_updated_at_str.replace("Z", "+00:00"))
                    except (ValueError, TypeError) as e:
                        logger.error(f"解析远程更新时间失败: {str(e)}, permalink: {permalink}")

                # 如果远程版本更新，或者本地项被软删除了（需要恢复）
                needs_update = (remote_updated_at and (not item.remote_updated_at or remote_updated_at > item.remote_updated_at)) or item.is_deleted

                if needs_update:
                    update_data = {
                        "title": note_data.get("title", item.title),
                        "content": note_data.get("content", item.content),
                        "content_type": note_data.get("content_type", item.content_type),
                        "folder": folder,
                        "tags": note_data.get("tags", item.tags),
                        "source": note_data.get("source", item.source),
                        "remote_updated_at": remote_updated_at,
                        "sync_status": SyncStatus.SYNCED,
                        "is_deleted": False,  # 确保未删除
                    }
                    item = self.update_item(item.id, **update_data)
                    logger.info(f"从远程更新/恢复记忆项: {item.title}")

            self.session.commit()  # 确保提交事务
            return item, is_new
        except Exception as e:
            self.session.rollback()
            logger.error(f"同步记忆项失败: {str(e)}, permalink: {permalink}")
            raise

    def mark_item_synced(self, item_id: int, permalink: Optional[str] = None, remote_updated_at: Optional[datetime] = None) -> bool:
        """标记记忆项为已同步 (来自 helpers.sync_utils.mark_item_synced)

        Args:
            item_id: 记忆项ID
            permalink: 同步后的永久链接，如果有
            remote_updated_at: 远程更新时间，如果有

        Returns:
            bool: 是否成功
        """
        update_data = {"sync_status": SyncStatus.SYNCED}
        if permalink:
            # 确保permalink格式正确
            if not is_permalink(permalink):
                permalink = path_to_permalink(permalink)
            update_data["permalink"] = permalink
        if remote_updated_at:
            update_data["remote_updated_at"] = remote_updated_at

        try:
            item = self.update_item(item_id, **update_data)
            if item:
                logger.info(f"标记记忆项已同步: {item.title} (ID={item_id})")
                return True
            else:
                logger.warning(f"标记同步状态失败: 未找到ID为{item_id}的活动记忆项")
                return False
        except Exception as e:
            # update_item 内部已处理回滚和日志
            logger.error(f"标记同步状态失败 (ID={item_id}): {str(e)}")
            # Reraise the exception if needed or return False
            # raise  # Uncomment if the caller needs to handle the exception
            return False

    def get_unsynced_items(self) -> List[MemoryItem]:
        """获取所有未同步的记忆项 (来自 helpers.sync_utils.get_unsynced_items)

        Returns:
            List[MemoryItem]: 未同步的记忆项列表 (包括新增、修改、软删除)
        """
        try:
            # NOT_SYNCED 状态包括了新增、修改和软删除的项
            items = self.session.query(MemoryItem).filter(MemoryItem.sync_status == SyncStatus.NOT_SYNCED).all()
            return items
        except Exception as e:
            logger.error(f"获取未同步记忆项失败: {str(e)}")
            raise

    def list_folders(self) -> List[str]:
        """获取所有活动记忆项的文件夹列表 (来自 helpers.stats_utils.list_folders)

        Returns:
            List[str]: 文件夹名称列表
        """
        try:
            folders = self.session.query(MemoryItem.folder).filter(MemoryItem.is_deleted == False).distinct().all()
            return sorted([folder[0] for folder in folders if folder[0]])  # 过滤空文件夹名并排序
        except Exception as e:
            logger.error(f"获取文件夹列表失败: {str(e)}")
            raise

    def get_item_count(self, include_deleted: bool = False) -> int:
        """获取记忆项数量 (来自 helpers.stats_utils.get_item_count)

        Args:
            include_deleted: 是否包含已删除的记忆项

        Returns:
            int: 记忆项数量
        """
        try:
            query = self.session.query(func.count(MemoryItem.id))
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            return query.scalar()
        except Exception as e:
            logger.error(f"获取记忆项数量失败: {str(e)}")
            raise

    def get_db_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息 (来自 helpers.stats_utils.get_db_info)

        Returns:
            Dict[str, Any]: 数据库统计信息
        """
        try:
            total_count = self.get_item_count(include_deleted=True)
            active_count = self.get_item_count(include_deleted=False)
            deleted_count = total_count - active_count
            unsynced_count = self.session.query(func.count(MemoryItem.id)).filter(MemoryItem.sync_status == SyncStatus.NOT_SYNCED).scalar()

            # 获取所有不同的文件夹及计数
            folder_counts = (
                self.session.query(MemoryItem.folder, func.count(MemoryItem.id))
                .filter(MemoryItem.is_deleted == False)
                .group_by(MemoryItem.folder)
                .all()
            )

            # 转换为字典格式
            folder_counts_dict = {folder: count for folder, count in folder_counts if folder}

            # 获取文件夹列表
            folder_list = sorted(folder_counts_dict.keys())

            return {
                # "db_path": db_path, # db_path 不应由 repo 管理
                "total_items": total_count,
                "active_items": active_count,
                "deleted_items": deleted_count,
                "unsynced_items": unsynced_count,
                "folders": folder_list,
                "folder_counts": folder_counts_dict,
            }
        except Exception as e:
            logger.error(f"获取数据库统计信息失败: {str(e)}")
            raise

    # --- 以下是原有 Repository 中的方法，检查是否需要保留或修改 ---

    # def create(...) -> 已被 create_item 替代并增强

    def search_by_content(self, query: str, include_deleted: bool = False) -> List[MemoryItem]:
        """通过内容或标题或标签搜索记忆项 (修改自原有方法)

        Args:
            query: 搜索关键词
            include_deleted: 是否包含已删除项

        Returns:
            List[MemoryItem]: 匹配的记忆项列表
        """
        try:
            filters = [
                or_(
                    MemoryItem.title.ilike(f"%{query}%"),
                    MemoryItem.content.ilike(f"%{query}%"),
                    MemoryItem.tags.ilike(f"%{query}%"),  # 假设标签是逗号分隔，简单匹配
                )
            ]
            if not include_deleted:
                filters.append(MemoryItem.is_deleted == False)

            return self.session.query(MemoryItem).filter(and_(*filters)).order_by(MemoryItem.updated_at.desc()).all()  # 添加排序
        except Exception as e:
            logger.error(f"内容搜索失败: {str(e)}")
            raise

    # find_by_category, find_by_storage_type, find_by_refs, update_refs: 这些方法似乎不再被使用，
    # 并且 MemoryItem 模型中没有 category, storage_type, entity_refs 等字段。
    # 如果确认不再需要，可以删除。暂时注释掉。
    # def find_by_category(...)
    # def find_by_storage_type(...)
    # def find_by_refs(...)
    # def update_refs(...)

    def get_all(self, limit: int = 100, offset: int = 0, include_deleted: bool = False) -> List[MemoryItem]:
        """
        获取所有记忆项 (修改自原有方法)

        Args:
            limit: 限制返回数量
            offset: 偏移量
            include_deleted: 是否包含已删除项

        Returns:
            List[MemoryItem]: 记忆项列表
        """
        try:
            query = self.session.query(MemoryItem)
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            return query.order_by(desc(MemoryItem.updated_at)).limit(limit).offset(offset).all()  # 按更新时间排序
        except Exception as e:
            logger.error(f"获取所有记忆项失败: {str(e)}")
            raise

    # search_by_title(self, title: str, limit: int = 10) -> 已被 get_by_title 覆盖 (返回单个)
    # 如果需要模糊搜索并限制数量，可以保留或修改 search_items

    # search_by_tags(self, tags: List[str], limit: int = 10) -> 已被 search_items 覆盖
    # search_items 中的标签逻辑更灵活

    # update(self, memory_item_id: int, **kwargs) -> 已被 update_item 替代并增强

    # delete(self, memory_item_id: int) -> 已被 delete_item 替代并增强 (增加软删除)
