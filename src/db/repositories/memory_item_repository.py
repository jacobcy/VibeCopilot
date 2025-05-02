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
from src.models.db.memory_item import MemoryItem
from src.status.enums import SyncStatus  # 导入SyncStatus - 新路径

logger = logging.getLogger(__name__)


class MemoryItemRepository(Repository[MemoryItem]):
    """记忆项索引仓库类"""

    def __init__(self):
        """初始化仓库"""
        super().__init__(MemoryItem)

    def create_item(
        self,
        session: Session,
        title: str,
        content: str,  # 保留参数以保持兼容性，但不存储到数据库
        folder: str = "Inbox",
        tags: Optional[str] = None,
        permalink: Optional[str] = None,
        content_type: str = "text",
        source: Optional[str] = None,
        sync_status: SyncStatus = SyncStatus.NOT_SYNCED,
    ) -> Dict[str, Any]:
        """创建新的记忆项 (整合自 helpers.item_utils.create_memory_item)

        Args:
            session: SQLAlchemy会话对象
            title: 标题
            content: 内容（只用于生成摘要，不存储）
            folder: 文件夹，默认为Inbox
            tags: 标签（逗号分隔），可选
            permalink: Basic Memory中的永久链接，可选
            content_type: 内容类型，默认为text
            source: 来源，可选
            sync_status: 同步状态，默认未同步（注意：此参数保留但不直接使用，由模型表结构决定）

        Returns:
            Dict[str, Any]: 包含ID和title的字典
        """
        # 生成内容摘要
        summary = ""
        if content and len(content) > 50:  # 如果内容超过50个字符，生成摘要
            try:
                # 导入文本处理函数，避免循环导入
                from src.memory.helpers.text_helpers import extract_plain_text, truncate_text

                # 先提取纯文本，移除Markdown标记
                plain_text = extract_plain_text(content)
                # 截取前150个字符作为摘要
                summary = truncate_text(plain_text, 150, add_ellipsis=True)
                logger.info(f"生成内容摘要: {summary[:30]}...")
            except Exception as e:
                logger.warning(f"生成摘要失败: {str(e)}")
                # 如果失败，使用简单截取
                summary = content[:150] + "..." if len(content) > 150 else content
        else:
            # 如果内容很短，直接使用内容作为摘要
            summary = content or ""

        # 使用基础 Repository 的 create 方法
        data = {
            "title": title,
            "summary": summary,  # 摘要字段，必须有值
            "content_type": content_type,
            "folder": folder,
            "tags": tags,
            "permalink": permalink,
            "source": source,
            # 显式添加模型中定义的默认值，确保类型正确
            "is_deleted": False,
            "sync_status": sync_status.name if isinstance(sync_status, SyncStatus) else str(sync_status),
            "entity_count": 0,
            "relation_count": 0,
            "observation_count": 0,
            # created_at, updated_at, remote_updated_at, vector_updated_at 由数据库或模型处理
        }
        # 移除 None 值，让数据库或模型处理 nullable 字段
        data = {k: v for k, v in data.items() if v is not None}

        try:
            # 手动创建 MemoryItem 对象，确保类型正确
            item = MemoryItem(
                title=data.get("title"),
                summary=data.get("summary"),
                content_type=data.get("content_type", "text"),
                folder=data.get("folder", "Inbox"),
                tags=data.get("tags"),
                permalink=data.get("permalink"),
                source=data.get("source"),
                is_deleted=data.get("is_deleted", False),
                sync_status=data.get("sync_status", "NOT_SYNCED"),
                entity_count=data.get("entity_count", 0),
                relation_count=data.get("relation_count", 0),
                observation_count=data.get("observation_count", 0)
                # 其他字段让 SQLAlchemy 处理默认值或 nullable
            )
            session.add(item)
            session.flush()  # 确保对象获得 ID 并被添加到 session
            session.refresh(item)  # 刷新对象状态，确保ID等属性已加载
            # item = self.create(session, data) # 不再使用基类的 create
            logger.info(f"创建记忆项: {item.title} (文件夹: {folder})")
            # 返回字典而不是 ORM 对象，避免 DetachedInstanceError
            return {"id": item.id, "title": item.title}  # 返回包含 ID 和 title 的字典
        except Exception as e:
            logger.error(f"创建记忆项失败: {str(e)}")
            # session.rollback() # Rollback is handled by the session context manager now
            raise

    def get_by_id(self, session: Session, memory_item_id: int, include_deleted: bool = False) -> Optional[MemoryItem]:
        """
        根据ID获取记忆项 (整合自 helpers.item_utils.get_item_by_id)

        Args:
            session: SQLAlchemy会话对象
            memory_item_id: 记忆项ID
            include_deleted: 是否包含已删除项

        Returns:
            Optional[MemoryItem]: 找到的记忆项，如果不存在则返回None
        """
        try:
            query = session.query(MemoryItem).filter(MemoryItem.id == memory_item_id)
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            return query.first()
        except Exception as e:
            logger.error(f"获取记忆项失败 (ID={memory_item_id}): {str(e)}")
            raise

    def get_by_permalink(self, session: Session, permalink: str, include_deleted: bool = False) -> Optional[MemoryItem]:
        """通过永久链接获取记忆项 (来自 helpers.item_utils.get_item_by_permalink)

        Args:
            session: SQLAlchemy会话对象
            permalink: Basic Memory中的永久链接
            include_deleted: 是否包含已删除项

        Returns:
            Optional[MemoryItem]: 找到的记忆项，如果不存在则返回None
        """
        try:
            query = session.query(MemoryItem).filter(MemoryItem.permalink == permalink)
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            return query.first()
        except Exception as e:
            logger.error(f"获取记忆项失败 (permalink={permalink}): {str(e)}")
            raise

    def get_by_title(self, session: Session, title: str, include_deleted: bool = False) -> Optional[MemoryItem]:
        """通过标题获取记忆项 (来自 helpers.sync_utils.get_item_by_title)

        Args:
            session: SQLAlchemy会话对象
            title: 记忆项标题
            include_deleted: 是否包含已删除项

        Returns:
            Optional[MemoryItem]: 找到的记忆项，如果不存在则返回None
        """
        try:
            query = session.query(MemoryItem).filter(MemoryItem.title == title)
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            return query.first()
        except Exception as e:
            logger.error(f"获取记忆项失败 (title={title}): {str(e)}")
            raise

    def update_item(self, session: Session, memory_item_id: int, **kwargs) -> Optional[MemoryItem]:
        """
        更新记忆项 (整合自 helpers.item_utils.update_memory_item 和 repo.update)

        Args:
            session: SQLAlchemy会话对象
            memory_item_id: 记忆项ID
            **kwargs: 要更新的字段

        Returns:
            Optional[MemoryItem]: 更新后的记忆项，如果不存在则返回None
        """
        try:
            # 获取未删除的项
            item = self.get_by_id(session, memory_item_id, include_deleted=False)

            if not item:
                logger.warning(f"更新记忆项失败: 未找到ID为{memory_item_id}的活动记忆项")
                return None

            # 如果没有显式传入 sync_status，则标记为未同步
            if "sync_status" not in kwargs:
                item.sync_status = "NOT_SYNCED"  # 使用字符串而不是SyncStatus.NOT_SYNCED

            # 更新字段
            updated = False
            for key, value in kwargs.items():
                if hasattr(item, key) and getattr(item, key) != value:
                    # 如果是sync_status枚举，转换为字符串
                    if key == "sync_status" and isinstance(value, SyncStatus):
                        value = value.name
                    setattr(item, key, value)
                    updated = True

            # 只有在实际更新了字段时才提交
            if updated:
                session.commit()
                logger.info(f"更新记忆项: {item.title} (ID={memory_item_id})")
            else:
                logger.info(f"记忆项无需更新: {item.title} (ID={memory_item_id})")
            return item
        except Exception as e:
            session.rollback()
            logger.error(f"更新记忆项失败 (ID={memory_item_id}): {str(e)}")
            raise

    def delete_item(self, session: Session, memory_item_id: int, soft_delete: bool = True) -> bool:
        """
        删除记忆项 (整合自 helpers.item_utils.delete_memory_item 和 repo.delete)

        Args:
            session: SQLAlchemy会话对象
            memory_item_id: 记忆项ID
            soft_delete: 是否使用软删除，默认为True

        Returns:
            bool: 删除是否成功
        """
        try:
            # 获取项目，无论是否已删除，以便硬删除
            item = self.get_by_id(session, memory_item_id, include_deleted=True)

            if not item:
                logger.warning(f"删除记忆项失败: 未找到ID为{memory_item_id}的记忆项")
                return False

            if soft_delete:
                if not item.is_deleted:  # 避免重复软删除
                    item.is_deleted = True
                    item.sync_status = "NOT_SYNCED"  # 使用字符串而不是SyncStatus.NOT_SYNCED
                    session.commit()
                    logger.info(f"软删除记忆项: {item.title} (ID={memory_item_id})")
                else:
                    logger.info(f"记忆项已软删除: {item.title} (ID={memory_item_id})")
            else:
                session.delete(item)
                session.commit()
                logger.info(f"硬删除记忆项: {item.title} (ID={memory_item_id})")

            return True
        except Exception as e:
            session.rollback()
            logger.error(f"删除记忆项失败 (ID={memory_item_id}): {str(e)}")
            raise

    def search_items(
        self, session: Session, query: str = "", folder: Optional[str] = None, tags: Optional[str] = None, include_deleted: bool = False
    ) -> List[MemoryItem]:
        """搜索记忆项 (来自 helpers.item_utils.search_memory_items)

        Args:
            session: SQLAlchemy会话对象
            query: 搜索关键词，会匹配标题和内容
            folder: 限定文件夹
            tags: 限定标签
            include_deleted: 是否包含已删除的记忆项

        Returns:
            List[MemoryItem]: 符合条件的记忆项列表
        """
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
            items_query = session.query(MemoryItem)
            if filters:
                items_query = items_query.filter(and_(*filters))

            # 按更新时间排序
            items = items_query.order_by(MemoryItem.updated_at.desc()).all()

            return items
        except Exception as e:
            logger.error(f"搜索记忆项失败: {str(e)}")
            raise

    def sync_item_from_remote(self, session: Session, note_data: Dict[str, Any]) -> Tuple[MemoryItem, bool]:
        """从远程笔记数据同步记忆项 (来自 helpers.sync_utils.sync_item_from_remote)

        如果本地存在对应记忆项则更新，否则创建新记忆项

        Args:
            session: SQLAlchemy会话对象
            note_data: Basic Memory笔记数据

        Returns:
            Tuple[MemoryItem, bool]: 同步后的记忆项和是否是新创建的标志
        """
        permalink = note_data.get("permalink")
        if not permalink:
            raise ValueError("同步记忆项失败: 远程笔记数据缺少permalink")

        # 处理文件夹路径
        folder = note_data.get("folder", "Inbox")

        try:
            # 查找本地是否存在
            item = self.get_by_permalink(session, permalink, include_deleted=True)  # 包含已删除项，以便恢复

            is_new = False
            # 不存在则创建
            if not item:
                # 生成内容摘要
                content = note_data.get("content", "")
                summary = ""
                if content and len(content) > 50:  # 如果内容超过50个字符，生成摘要
                    try:
                        # 导入文本处理函数，避免循环导入
                        from src.memory.helpers.text_helpers import extract_plain_text, truncate_text

                        # 先提取纯文本，移除Markdown标记
                        plain_text = extract_plain_text(content)
                        # 截取前150个字符作为摘要
                        summary = truncate_text(plain_text, 150, add_ellipsis=True)
                        logger.info(f"生成内容摘要: {summary[:30]}...")
                    except Exception as e:
                        logger.warning(f"生成摘要失败: {str(e)}")
                        # 如果失败，使用简单截取
                        summary = content[:150] + "..." if len(content) > 150 else content
                else:
                    # 如果内容很短，直接使用内容作为摘要
                    summary = content or ""

                # 创建记忆项
                data = {
                    "title": note_data.get("title", "Untitled"),
                    "summary": summary,  # 摘要字段，必须有值
                    "content_type": note_data.get("content_type", "text"),
                    "folder": folder,
                    "tags": note_data.get("tags"),
                    "source": note_data.get("source"),
                    "permalink": permalink,
                    "sync_status": SyncStatus.SYNCED.name,  # 从远程同步过来的，初始状态就是 SYNCED
                }
                item = self.create_item(session, **data)
                is_new = True
                logger.info(f"从远程创建记忆项: {item['title']}")
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
                    # 生成内容摘要
                    content = note_data.get("content", "")
                    summary = ""
                    if content and len(content) > 50:  # 如果内容超过50个字符，生成摘要
                        try:
                            # 导入文本处理函数，避免循环导入
                            from src.memory.helpers.text_helpers import extract_plain_text, truncate_text

                            # 先提取纯文本，移除Markdown标记
                            plain_text = extract_plain_text(content)
                            # 截取前150个字符作为摘要
                            summary = truncate_text(plain_text, 150, add_ellipsis=True)
                            logger.info(f"生成内容摘要: {summary[:30]}...")
                        except Exception as e:
                            logger.warning(f"生成摘要失败: {str(e)}")
                            # 如果失败，使用简单截取
                            summary = content[:150] + "..." if len(content) > 150 else content
                    else:
                        # 如果内容很短，直接使用内容作为摘要
                        summary = content or ""

                    update_data = {
                        "title": note_data.get("title", item.title),
                        "summary": summary,  # 摘要字段，必须有值
                        "content_type": note_data.get("content_type", item.content_type),
                        "folder": folder,
                        "tags": note_data.get("tags", item.tags),
                        "source": note_data.get("source", item.source),
                        "remote_updated_at": remote_updated_at,
                        "sync_status": "SYNCED",  # 使用字符串而不是SyncStatus.SYNCED
                        "is_deleted": False,  # 确保未删除
                    }
                    item = self.update_item(session, item.id, **update_data)
                    logger.info(f"从远程更新/恢复记忆项: {item['title']}")

            session.commit()  # 确保提交事务
            return item, is_new
        except Exception as e:
            session.rollback()
            logger.error(f"同步记忆项失败: {str(e)}, permalink: {permalink}")
            raise

    def mark_item_synced(self, session: Session, item_id: int, permalink: Optional[str] = None, remote_updated_at: Optional[datetime] = None) -> bool:
        """标记记忆项为已同步 (来自 helpers.sync_utils.mark_item_synced)

        Args:
            session: SQLAlchemy会话对象
            item_id: 记忆项ID
            permalink: 同步后的永久链接，如果有
            remote_updated_at: 远程更新时间，如果有

        Returns:
            bool: 是否成功
        """
        update_data = {"sync_status": "SYNCED"}  # 使用字符串而不是SyncStatus.SYNCED
        if permalink:
            update_data["permalink"] = permalink
        if remote_updated_at:
            update_data["remote_updated_at"] = remote_updated_at

        try:
            item = self.update_item(session, item_id, **update_data)
            if item:
                logger.info(f"标记记忆项已同步: {item['title']} (ID={item_id})")
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

    def get_unsynced_items(self, session: Session) -> List[MemoryItem]:
        """获取所有未同步的记忆项 (来自 helpers.sync_utils.get_unsynced_items)

        Returns:
            List[MemoryItem]: 未同步的记忆项列表 (包括新增、修改、软删除)
        """
        try:
            # 使用字符串而不是SyncStatus.NOT_SYNCED
            items = session.query(MemoryItem).filter(MemoryItem.sync_status == "NOT_SYNCED").all()
            return items
        except Exception as e:
            logger.error(f"获取未同步记忆项失败: {str(e)}")
            raise

    def list_folders(self, session: Session) -> List[str]:
        """获取所有活动记忆项的文件夹列表 (来自 helpers.stats_utils.list_folders)

        Returns:
            List[str]: 文件夹名称列表
        """
        try:
            folders = session.query(MemoryItem.folder).filter(MemoryItem.is_deleted == False).distinct().all()
            return sorted([folder[0] for folder in folders if folder[0]])  # 过滤空文件夹名并排序
        except Exception as e:
            logger.error(f"获取文件夹列表失败: {str(e)}")
            raise

    def get_item_count(self, session: Session, include_deleted: bool = False) -> int:
        """获取记忆项数量 (来自 helpers.stats_utils.get_item_count)

        Args:
            session: SQLAlchemy会话对象
            include_deleted: 是否包含已删除的记忆项

        Returns:
            int: 记忆项数量
        """
        try:
            query = session.query(func.count(MemoryItem.id))
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            return query.scalar()
        except Exception as e:
            logger.error(f"获取记忆项数量失败: {str(e)}")
            raise

    def get_db_stats(self, session: Session) -> Dict[str, Any]:
        """获取数据库统计信息 (来自 helpers.stats_utils.get_db_info)

        Returns:
            Dict[str, Any]: 数据库统计信息
        """
        try:
            total_count = self.get_item_count(session, include_deleted=True)
            active_count = self.get_item_count(session, include_deleted=False)
            deleted_count = total_count - active_count
            unsynced_count = session.query(func.count(MemoryItem.id)).filter(MemoryItem.sync_status == SyncStatus.NOT_SYNCED).scalar()

            # 获取所有不同的文件夹及计数
            folder_counts = (
                session.query(MemoryItem.folder, func.count(MemoryItem.id)).filter(MemoryItem.is_deleted == False).group_by(MemoryItem.folder).all()
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

    def get_folder_stats(self, session: Session, include_deleted: bool = False) -> Dict[str, int]:
        """获取文件夹统计信息"""
        try:
            query = session.query(MemoryItem.folder, func.count(MemoryItem.id)).group_by(MemoryItem.folder)
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            stats = {folder: count for folder, count in query.all()}
            return stats
        except Exception as e:
            logger.error(f"获取文件夹统计失败: {str(e)}")
            raise

    def get_tag_stats(self, session: Session, include_deleted: bool = False) -> Dict[str, int]:
        """获取标签统计信息（注意：标签是逗号分隔的字符串）"""
        try:
            # 这种方式效率不高，但对于SQLite足够
            query = session.query(MemoryItem.tags)
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)

            tag_counts: Dict[str, int] = {}
            for (tags_str,) in query.all():
                if tags_str:
                    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            return tag_counts
        except Exception as e:
            logger.error(f"获取标签统计失败: {str(e)}")
            raise

    def get_last_updated_time(self, session: Session, include_deleted: bool = False) -> Optional[datetime]:
        """获取最后一个更新的记忆项时间"""
        try:
            query = session.query(func.max(MemoryItem.updated_at))
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            last_updated = query.scalar()
            return last_updated
        except Exception as e:
            logger.error(f"获取最后更新时间失败: {str(e)}")
            raise

    def search_by_content(self, session: Session, query: str, include_deleted: bool = False) -> List[MemoryItem]:
        """通过内容或标题或标签搜索记忆项 (修改自原有方法)

        Args:
            session: SQLAlchemy会话对象
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

            return session.query(MemoryItem).filter(and_(*filters)).order_by(MemoryItem.updated_at.desc()).all()  # 添加排序
        except Exception as e:
            logger.error(f"内容搜索失败: {str(e)}")
            raise

    def get_all(self, session: Session, limit: int = 100, offset: int = 0, include_deleted: bool = False) -> List[MemoryItem]:
        """
        获取所有记忆项 (修改自原有方法)

        Args:
            session: SQLAlchemy会话对象
            limit: 限制返回数量
            offset: 偏移量
            include_deleted: 是否包含已删除项

        Returns:
            List[MemoryItem]: 记忆项列表
        """
        try:
            query = session.query(MemoryItem)
            if not include_deleted:
                query = query.filter(MemoryItem.is_deleted == False)
            return query.order_by(desc(MemoryItem.updated_at)).limit(limit).offset(offset).all()  # 按更新时间排序
        except Exception as e:
            logger.error(f"获取所有记忆项失败: {str(e)}")
            raise

    def find_by_permalink(self, session: Session, permalink: str, include_deleted: bool = False) -> Optional[MemoryItem]:
        """通过永久链接获取记忆项 (get_by_permalink的别名)

        Args:
            session: SQLAlchemy会话对象
            permalink: Basic Memory中的永久链接
            include_deleted: 是否包含已删除项

        Returns:
            Optional[MemoryItem]: 找到的记忆项，如果不存在则返回None
        """
        return self.get_by_permalink(session, permalink, include_deleted)

    def find_by_folder(self, session: Session, folder: str, limit: int = 100, include_deleted: bool = False) -> List[MemoryItem]:
        """通过文件夹获取记忆项列表 (search_items的包装方法)

        Args:
            session: SQLAlchemy会话对象
            folder: 文件夹名称
            limit: 返回记录数量限制
            include_deleted: 是否包含已删除项

        Returns:
            List[MemoryItem]: 找到的记忆项列表
        """
        items = self.search_items(session, query="", folder=folder, include_deleted=include_deleted)
        return items[:limit] if items and len(items) > limit else items

    def create(self, session: Session, data: Dict[str, Any]) -> MemoryItem:
        """覆盖基类 create 方法以添加 session 参数和 ID 生成"""
        if "id" not in data:
            from src.utils.id_generator import EntityType, IdGenerator

            data["id"] = IdGenerator.generate_id(EntityType.MEMORY_ITEM)
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow()
        if "updated_at" not in data:
            data["updated_at"] = data["created_at"]
        if "summary" not in data:
            data["summary"] = data.get("title", "")[:150]
        if "sync_status" not in data:
            data["sync_status"] = SyncStatus.NOT_SYNCED.name

        entity = self.model_class(**data)
        session.add(entity)
        return entity

    def update(self, session: Session, entity_id: int, data: Dict[str, Any]) -> Optional[MemoryItem]:
        """覆盖基类 update 方法以添加 session 参数"""
        entity = self.get_by_id(session, entity_id)
        if entity:
            data["updated_at"] = datetime.utcnow()  # Ensure updated_at is set
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
                else:
                    logger.warning(f"尝试更新不存在的属性 {key} for {self.model.__name__}")
            # No commit needed
            return entity
        return None

    def delete(self, session: Session, entity_id: int) -> bool:
        """覆盖基类 delete 方法以添加 session 参数 (硬删除)"""
        return self.delete_item(session, entity_id, soft_delete=False)  # Reuse delete_item for logic
