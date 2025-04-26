#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
笔记服务 - 负责笔记的创建、读取、更新和删除

封装Basic Memory相关操作的实现细节，提供简洁的API接口。
实现本地缓存以提高性能，并与远程Basic Memory系统保持同步。
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

# Remove: from src.db.service import DatabaseService
from src.db.repositories.memory_item_repository import MemoryItemRepository  # <-- Import Repository
from src.db.session_manager import session_scope  # <-- Import session_scope

# 导入工具函数
from ..helpers import is_permalink, normalize_path, path_to_permalink  # 移除数据库工具; init_db_engine, create_tables, get_session,; 路径和URL工具
from ..helpers.note_utils import _extract_folder, _generate_path_variants, create_note, delete_note, read_note, update_note

# 移除db_utils和repository的直接导入
# from ..helpers.db_utils import init_db_engine, get_session
# from src.db.repositories.memory_item_repository import MemoryItemRepository


logger = logging.getLogger(__name__)


class NoteService:
    """笔记服务，处理笔记的CRUD操作，支持本地缓存和远程同步"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化笔记服务

        Args:
            config: 可选配置参数
        """
        self.config = config or {}
        self.memory_root = os.path.expanduser(self.config.get("memory_root", "/Volumes/Cube/VibeCopilot/.ai/memory"))
        self.project = self.config.get("project", "vibecopilot")

        # Remove: self.db_service = DatabaseService()
        self._memory_item_repo = MemoryItemRepository()  # <-- Instantiate Repository

    def create_note(self, content: str, title: str, folder: str, tags: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        创建新笔记，同时保存到远程和本地

        Args:
            content: 笔记内容
            title: 笔记标题
            folder: 存储目录
            tags: 标签列表（逗号分隔）

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        logger.info(f"创建笔记: {title} 到 {folder}")

        # 首先创建到远程Basic Memory
        success, message, result = create_note(content, title, folder, tags, self.project)

        # 如果远程创建成功，同时保存到本地数据库
        if success:
            try:
                permalink = result.get("permalink", "")
                with session_scope() as session:  # <-- Use session_scope
                    self._memory_item_repo.create_item(  # <-- Use self._memory_item_repo
                        session=session, title=title, content=content, folder=folder, tags=tags, permalink=permalink  # <-- Pass session
                    )
                message += "\n同时已保存到本地数据库"
            except Exception as e:
                logger.error(f"保存到本地数据库失败: {str(e)}")
                message += f"\n警告: 已保存到远程，但本地保存失败: {str(e)}"

        return success, message, result

    def read_note(self, path: str, use_local: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
        """
        读取笔记内容，优先从本地数据库读取，失败时从远程获取

        Args:
            path: 笔记路径或标识符
            use_local: 是否优先使用本地数据库

        Returns:
            元组，包含(是否成功, 内容, 元数据)
        """
        logger.info(f"读取笔记: {path}, 优先使用本地: {use_local}")

        # 尝试从本地数据库读取
        if use_local:
            try:
                with session_scope() as session:  # <-- Use session_scope
                    # 尝试通过permalink获取
                    item = self._memory_item_repo.get_by_permalink(session=session, permalink=path)  # <-- Use self._memory_item_repo & pass session

                    if item and not item.is_deleted:
                        logger.info(f"从本地数据库读取: {path}")
                        content = item.content
                        metadata = {
                            "title": item.title,
                            "folder": item.folder,
                            "tags": item.tags,
                            "permalink": item.permalink,
                            "content": content,
                            "source": "local",
                        }
                        return True, content, metadata

                    # 如果通过permalink找不到，尝试通过标题查找
                    if not item and "/" in path:
                        title = path.split("/")[-1]
                        if "." in title:
                            title = title.split(".")[0]

                        # 将下划线转换为空格，可能更符合标题格式
                        title = title.replace("_", " ")
                        item = self._memory_item_repo.get_by_title(session=session, title=title)  # <-- Use self._memory_item_repo & pass session

                        if item and not item.is_deleted:
                            logger.info(f"通过标题从本地数据库读取: {title}")
                            content = item.content
                            metadata = {
                                "title": item.title,
                                "folder": item.folder,
                                "tags": item.tags,
                                "permalink": item.permalink,
                                "content": content,
                                "source": "local",
                            }
                            return True, content, metadata
            except Exception as e:
                logger.error(f"从本地数据库读取失败: {str(e)}")

        # 从远程读取，利用note_utils中的read_note方法
        logger.info(f"从远程读取笔记: {path}")
        success, content, metadata = read_note(path, self.project)

        # 如果远程读取成功，且本地无缓存，则保存到本地
        if success and use_local:
            try:
                with session_scope() as session:  # <-- Use session_scope
                    item = self._memory_item_repo.get_by_permalink(
                        session=session, permalink=metadata.get("permalink", path)
                    )  # <-- Use self._memory_item_repo & pass session

                    if not item:
                        # 如果本地不存在，创建新记录
                        permalink = metadata.get("permalink", path)
                        title = metadata.get("title", os.path.basename(path))
                        folder = metadata.get("folder", "notes")
                        tags = metadata.get("tags")
                        if isinstance(tags, list):
                            tags = ",".join(tags)

                        self._memory_item_repo.create_item(  # <-- Use self._memory_item_repo
                            session=session,  # <-- Pass session
                            title=title,
                            content=content,
                            folder=folder,
                            tags=tags,
                            permalink=permalink,
                            sync_status="SYNCED",  # 从远程获取的，视为已同步
                        )
                        logger.info(f"已将远程内容缓存到本地: {path}")
            except Exception as e:
                logger.error(f"缓存到本地失败: {str(e)}")
                # Repository内部会处理回滚

        if success:
            metadata["source"] = "remote"

        return success, content, metadata

    def update_note(self, path: str, content: str, tags: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        更新笔记内容，同时更新远程和本地

        Args:
            path: 笔记路径或标识符
            content: 更新后的内容
            tags: 更新的标签（逗号分隔）

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        logger.info(f"更新笔记: {path}")

        # 首先更新远程，利用note_utils中的update_note方法
        success, message, result = update_note(path, content, tags, self.project)

        # 如果远程更新成功，同时更新本地数据库
        if success:
            try:
                with session_scope() as session:  # <-- Use session_scope
                    permalink = result.get("permalink", path)
                    item = self._memory_item_repo.get_by_permalink(
                        session=session, permalink=permalink
                    )  # <-- Use self._memory_item_repo & pass session

                    if item:
                        self._memory_item_repo.update_item(
                            session=session, item_id=item.id, content=content, tags=tags, sync_status="SYNCED"
                        )  # <-- Use self._memory_item_repo & pass session
                        message += "\n同时已更新本地数据库"
                    else:
                        # 如果本地不存在，则创建
                        title = result.get("title", os.path.basename(path))
                        folder = result.get("folder", "notes")

                        self._memory_item_repo.create_item(  # <-- Use self._memory_item_repo
                            session=session,  # <-- Pass session
                            title=title,
                            content=content,
                            folder=folder,
                            tags=tags,
                            permalink=permalink,
                            sync_status="SYNCED",  # 从远程更新的，视为已同步
                        )
                        message += "\n已创建本地缓存"
            except Exception as e:
                logger.error(f"更新本地数据库失败: {str(e)}")
                message += f"\n警告: 已更新远程，但本地更新失败: {str(e)}"
                # Repository内部会处理回滚

        return success, message, result

    def delete_note(self, path: str, force: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        """
        删除笔记，删除本地文件和数据库记录

        Args:
            path: 笔记路径或标识符
            force: 是否强制删除

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        logger.info(f"删除笔记: {path}, 强制: {force}")

        # 1. 先尝试删除本地文件
        # 确保路径有.md后缀
        file_path = path
        if not file_path.endswith(".md"):
            file_path = file_path + ".md"

        # 删除本地文件
        success, message, result = delete_note(path, self.memory_root, force, self.project)

        # 2. 删除数据库记录
        try:
            with session_scope() as session:  # <-- Use session_scope
                # 通过Repository访问MemoryItemRepository
                repo = self._memory_item_repo

                # 尝试获取本地记录
                # 如果路径以.md结尾，移除后缀再查询
                db_path = path
                if db_path.endswith(".md"):
                    db_path = db_path[:-3]

                item = repo.get_by_permalink(session=session, permalink=db_path)

                if item:
                    # 软删除本地记录
                    repo.delete_item(session=session, item_id=item.id, soft_delete=True)
                    message += "\n同时已在本地数据库中标记为删除"
        except Exception as e:
            logger.error(f"更新本地数据库删除状态失败: {str(e)}")
            message += f"\n警告: 已删除文件，但更新本地状态失败: {str(e)}"

        return success, message, result

    def search_notes(self, query: str, use_local: bool = True) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        搜索笔记

        Args:
            query: 搜索关键词
            use_local: 是否使用本地搜索

        Returns:
            元组，包含(是否成功, 消息, 搜索结果)
        """
        logger.info(f"搜索笔记: {query}, 使用本地: {use_local}")

        results = []
        message = ""

        if use_local:
            try:
                with session_scope() as session:  # <-- Use session_scope
                    # 通过Repository访问MemoryItemRepository
                    repo = self._memory_item_repo

                    # 从本地数据库搜索
                    items = repo.search_items(session=session, query=query)

                    for item in items:
                        if item.is_deleted:
                            continue

                        # 截断内容预览
                        content_preview = item.content[:200] + "..." if len(item.content) > 200 else item.content

                        results.append(
                            {
                                "title": item.title,
                                "content": content_preview,
                                "folder": item.folder,
                                "tags": item.tags,
                                "permalink": item.permalink,
                                "source": "local",
                            }
                        )

                    message = f"共找到 {len(results)} 条结果"
                    return True, message, results
            except Exception as e:
                logger.error(f"本地搜索失败: {str(e)}")
                message = f"本地搜索失败: {str(e)}"

        # 如果本地搜索失败或不使用本地，使用导入的search_service
        # 注意: 由于循环导入问题，这里动态导入
        try:
            from ..services.search_service import SearchService

            search_service = SearchService(self.config)
            success, message, remote_results = search_service.search_notes(query)

            if success:
                return success, message, remote_results
            else:
                return False, f"搜索失败: {message}", []

        except Exception as e:
            logger.error(f"远程搜索失败: {str(e)}")
            return False, f"搜索失败: {str(e)}", []

    def sync_with_remote(self, notes: List[Dict[str, Any]]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        将远程笔记同步到本地数据库

        Args:
            notes: 远程笔记列表

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        logger.info(f"同步远程笔记到本地，共 {len(notes)} 条")

        created_count = 0
        updated_count = 0
        error_count = 0

        try:
            with session_scope() as session:  # <-- Use session_scope
                # 通过Repository访问MemoryItemRepository
                repo = self._memory_item_repo

                for note_data in notes:
                    permalink = note_data.get("permalink")
                    if not permalink:
                        logger.warning(f"忽略没有permalink的笔记: {note_data.get('title', 'Unknown')}")
                        error_count += 1
                        continue

                    try:
                        # 让 Repository 处理同步逻辑
                        item, is_new = repo.sync_item_from_remote(session=session, note_data=note_data)
                        if is_new:
                            created_count += 1
                        else:
                            updated_count += 1

                    except Exception as e:
                        logger.error(f"同步单个笔记失败: {str(e)}, 笔记: {permalink}")
                        error_count += 1

                message = f"同步完成: 创建 {created_count} 条, 更新 {updated_count} 条, 失败 {error_count} 条"
                return True, message, {"created": created_count, "updated": updated_count, "failed": error_count}
        except Exception as e:
            error_message = f"同步远程笔记失败: {str(e)}"
            logger.error(error_message)
            # Repository内部会处理回滚
            return False, error_message, {}
