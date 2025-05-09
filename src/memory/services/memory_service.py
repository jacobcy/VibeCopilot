#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一内存服务模块

提供对知识库功能的统一访问接口，作为内存操作的 Facade。
(重构完成：委托给 memory_operations)
"""

import logging
import os
import pathlib
from typing import Any, Dict, List, Optional, Tuple, Union

# --- 数据库和工具依赖 ---
from src.db.repositories.memory_item_repository import MemoryItemRepository
from src.db.session_manager import session_scope

# --- 导入操作逻辑 --- #
from src.memory.services.memory_operations import execute_create_note, execute_import_documents, execute_list_notes, execute_read_note

# --- 导入真实的工具封装层 --- #
from src.memory.tools.basic_memory_wrapper import BasicMemoryWrapper

# 移除对 note_utils 的依赖，逻辑移至 memory_operations
# from src.memory.helpers.note_utils import ...


# from src.tools.wrappers.filesystem_wrapper import FilesystemWrapper # 导入真实的 filesystem 封装


# --- 暂时使用 TODO 标记表示需要 Filesystem 真实实现 --- #
# FilesystemWrapper 的占位符定义现在移到 memory_operations.py 中，这里不再需要
# class TODO_FilesystemWrapper:
#     ...
# --- 结束 Filesystem TODO ---

logger = logging.getLogger(__name__)


class MemoryService:
    """统一内存服务类 (Facade)"""

    def __init__(self):
        """初始化统一内存服务"""
        self.logger = logging.getLogger(__name__)
        self._memory_item_repo = MemoryItemRepository()
        self.basic_memory = BasicMemoryWrapper()
        # self.filesystem = FilesystemWrapper() # 真实实现
        # 使用 memory_operations 导入的占位符类
        from src.memory.tools.filesystem_wrapper import TODO_FilesystemWrapper

        self.filesystem = TODO_FilesystemWrapper()  # 使用占位符

        self.project = "vibecopilot"  # TODO: 从配置加载
        try:
            self.memory_root_str = os.environ.get("VIBECOPILOT_MEMORY_PATH", "~/.ai/vibecopilot/memory/notes")
            self.memory_root = pathlib.Path(os.path.expanduser(self.memory_root_str))
            self.memory_root.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"MemoryService Facade initialized. Root: {self.memory_root}")
        except Exception as e:
            self.logger.exception(f"Error initializing memory root path '{self.memory_root_str}': {e}")
            raise RuntimeError(f"Failed to initialize memory service root path: {e}") from e

    # --- 标识符辅助函数 (保留在 Service 或移至 Operations 皆可，暂留此处) --- #
    # 如果 operations 内部不再需要直接访问 Service 的这些方法，可以移除
    def _get_identifier(self, folder: str, title: str) -> str:
        # 这里的实现应该与 operations 中的 _get_identifier 一致
        folder = folder.strip("/")
        title = title.strip()
        return f"{folder}/{title}" if folder else title

    def _get_file_path(self, identifier: str) -> pathlib.Path:
        # 这里的实现应该与 operations 中的 _get_file_path 一致
        safe_identifier = identifier
        return self.memory_root / f"{safe_identifier}.md"

    # ===== 笔记管理功能 (委托给 Operations) ===== #

    def create_note(self, content: str, title: str, folder: str, tags: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """创建新笔记 (委托给 execute_create_note)"""
        return execute_create_note(
            content=content,
            title=title,
            folder=folder,
            tags=tags,
            repo=self._memory_item_repo,
            basic_memory=self.basic_memory,
            memory_root=self.memory_root,
        )

    def read_note(self, path_or_permalink: str, use_local: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
        """读取笔记内容 (委托给 execute_read_note)"""
        return execute_read_note(
            path_or_permalink=path_or_permalink, repo=self._memory_item_repo, basic_memory=self.basic_memory, memory_root=self.memory_root
        )

    def delete_note(self, path_or_permalink: str, force: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        """删除内存项 (直接调用 BasicMemoryWrapper)"""
        self.logger.debug(f"Service: Deleting note via Wrapper - '{path_or_permalink}'")
        try:
            success, message, data = self.basic_memory.delete_note(identifier=path_or_permalink)
            return success, message, data
        except Exception as e:
            self.logger.exception(f"调用 BasicMemoryWrapper.delete_note 时发生错误: {e}")
            return False, f"删除笔记时发生内部错误: {str(e)}", {}

    # ===== 搜索功能 (直接调用 Wrapper) ===== #
    def search_notes(self, query: str, content_type: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """搜索知识库内容 (直接调用 Wrapper)"""
        # 搜索逻辑相对简单，可以直接调用 Wrapper
        self.logger.debug(f"Service: Searching notes - query='{query}', type='{content_type or 'any'}'")
        try:
            types_list = [content_type] if content_type else None
            success, msg, results = self.basic_memory.search_notes(query=query, types=types_list)
            if success:
                # 格式化消息移到这里，因为 operations 不再处理搜索
                user_msg = f"为 '{query}' 找到 {len(results)} 个结果:\n"
                if results:
                    formatted_list = []
                    for item in results:
                        identifier = item.get("identifier", "未知标识")
                        snippet = item.get("snippet", "无摘要")
                        score_str = f" (Score: {item.get('score'):.2f})" if item.get("score") is not None else ""
                        formatted_list.append(f"- {identifier}{score_str}: {snippet}")
                    user_msg += "\n".join(formatted_list)
                else:
                    user_msg = f"未能为 '{query}' 找到任何结果。"
                return True, user_msg.strip(), results  # 返回格式化后的消息
            else:
                self.logger.error(f"Basic Memory Wrapper 搜索失败: {msg}")
                return False, f"知识库工具搜索失败: {msg}", []
        except Exception as e:
            self.logger.exception(f"搜索笔记时发生意外错误: {e}")
            return False, f"搜索笔记时发生内部错误: {str(e)}", []

    # ===== 导入功能 (委托给 Operations) ===== #
    def import_documents(self, source_path: str, recursive: bool = False, target_folder_prefix: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        """从外部文件系统导入文档 (委托给 execute_import_documents)"""
        return execute_import_documents(
            source_path=source_path,
            repo=self._memory_item_repo,
            basic_memory=self.basic_memory,
            filesystem=self.filesystem,
            memory_root=self.memory_root,
            recursive=recursive,
            target_folder_prefix=target_folder_prefix,
        )

    # ===== 统计与状态 (直接访问 DB) ===== #
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息 (直接访问 DB)"""
        # 统计逻辑相对简单，保留在 Service 中
        self.logger.debug("Service: Getting memory stats")
        try:
            with session_scope() as session:
                total_items = self._memory_item_repo.count_items(session, include_deleted=False)
                deleted_items = self._memory_item_repo.count_items(session, include_deleted=True) - total_items
            sync_status = "local_only (功能待实现)"  # TODO: 实现同步状态检查
            stats = {"notes_count": total_items, "deleted_count": deleted_items, "sync_status": sync_status}
            self.logger.info(f"内存统计: {stats}")
            return stats
        except Exception as e:
            self.logger.exception(f"获取内存统计时出错: {e}")
            return {"error": f"获取统计失败: {str(e)}"}

    def list_notes(self, folder: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """列出笔记 (委托给 execute_list_notes)"""
        return execute_list_notes(repo=self._memory_item_repo, folder=folder)


# --- 单例模式 --- #
_memory_service_instance = None


def get_memory_service() -> MemoryService:
    """获取统一内存服务单例"""
    global _memory_service_instance
    if _memory_service_instance is None:
        _memory_service_instance = MemoryService()
    return _memory_service_instance
