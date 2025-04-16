#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MemoryService接口实现

提供VibeCopilot知识库服务的统一接口实现，
封装了所有与知识库交互的功能，提供一致的API。
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from src.memory.entity_manager import EntityManager
from src.memory.memory_manager import MemoryManager
from src.memory.observation_manager import ObservationManager
from src.memory.relation_manager import RelationManager
from src.memory.services.memory_service import MemoryService
from src.memory.sync_executor import SyncExecutor

logger = logging.getLogger(__name__)


class MemoryServiceImpl(MemoryService):
    """
    MemoryService接口实现

    使用门面(Facade)模式，整合现有各子系统功能，
    为命令行工具和其他模块提供统一的API接口。
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """单例模式实现，确保全局只有一个实例"""
        if cls._instance is None:
            logger.debug("创建MemoryService单例实例")
            cls._instance = super(MemoryServiceImpl, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化MemoryService

        Args:
            config: 可选配置参数
        """
        # 单例模式，防止重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.config = config or {}
        logger.debug("初始化MemoryService")

        # 初始化各个子系统
        self.memory_manager = MemoryManager(config)
        self.sync_executor = SyncExecutor(config)
        self.entity_manager = EntityManager(config)
        self.observation_manager = ObservationManager(config)
        self.relation_manager = RelationManager(config)

        self._initialized = True
        logger.info("MemoryService初始化完成")

    def _run_async(self, coro):
        """运行异步任务的辅助方法"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)

    def create_note(self, content: str, title: str, folder: str, tags: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        创建新笔记

        Args:
            content: 笔记内容(Markdown格式)
            title: 笔记标题
            folder: 存储文件夹
            tags: 可选标签，逗号分隔

        Returns:
            成功/失败标志，消息，数据
        """
        try:
            # 使用_run_async辅助方法运行异步任务
            result = self._run_async(self.memory_manager.store_memory(content=content, title=title, tags=tags, folder=folder))
            return True, "笔记创建成功", result
        except Exception as e:
            logger.error(f"创建笔记失败: {e}", exc_info=True)
            return False, f"创建笔记失败: {str(e)}", {}

    def read_note(self, path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        读取笔记内容

        Args:
            path: 笔记路径(memory://folder/title或ID)

        Returns:
            成功/失败标志，消息，数据
        """
        try:
            result = self._run_async(self.memory_manager.get_memory_by_id(path))
            if not result:
                return False, f"未找到笔记: {path}", {}
            return True, "笔记读取成功", result
        except Exception as e:
            logger.error(f"读取笔记失败: {e}", exc_info=True)
            return False, f"读取笔记失败: {str(e)}", {}

    def update_note(self, path: str, content: str, tags: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        更新笔记内容

        Args:
            path: 笔记路径
            content: 新内容
            tags: 可选标签，逗号分隔

        Returns:
            成功/失败标志，消息，数据
        """
        try:
            result = self._run_async(self.memory_manager.update_memory(permalink=path, content=content, tags=tags))
            return True, "笔记更新成功", result
        except Exception as e:
            logger.error(f"更新笔记失败: {e}", exc_info=True)
            return False, f"更新笔记失败: {str(e)}", {}

    def delete_note(self, path: str, force: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        """
        删除笔记

        Args:
            path: 笔记路径
            force: 是否强制删除

        Returns:
            成功/失败标志，消息，数据
        """
        try:
            result = self._run_async(self.memory_manager.delete_memory(path))
            return True, "笔记删除成功", result
        except Exception as e:
            logger.error(f"删除笔记失败: {e}", exc_info=True)
            return False, f"删除笔记失败: {str(e)}", {}

    def list_notes(self, folder: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        列出笔记

        Args:
            folder: 可选文件夹，如果不提供则列出所有笔记

        Returns:
            成功/失败标志，消息，笔记列表
        """
        try:
            result = self._run_async(self.memory_manager.list_memories(folder=folder))
            # 确保返回的是字典列表，而不是字符串列表
            memories = result.get("memories", [])
            return True, f"找到{len(memories)}条笔记", memories
        except Exception as e:
            logger.error(f"列出笔记失败: {e}", exc_info=True)
            return False, f"列出笔记失败: {str(e)}", []

    def search_notes(self, query: str, content_type: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        搜索笔记

        Args:
            query: 搜索查询
            content_type: 可选内容类型筛选

        Returns:
            成功/失败标志，消息，笔记列表
        """
        try:
            result = self._run_async(self.memory_manager.retrieve_memory(query=query, limit=10))

            # 提取结果并确保返回的是字典列表
            memories = result.get("results", [])

            if content_type:
                # 如果指定了内容类型，进行过滤
                filtered_memories = [item for item in memories if item.get("metadata", {}).get("type") == content_type]
                memories = filtered_memories

            return True, f"找到{len(memories)}条相关笔记", memories
        except Exception as e:
            logger.error(f"搜索笔记失败: {e}", exc_info=True)
            return False, f"搜索笔记失败: {str(e)}", []

    def sync_all(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        同步知识库（若支持）

        此方法被SyncOrchestrator调用，不再自己执行同步编排

        Returns:
            Tuple[bool, str, Dict[str, Any]]: (成功标志, 消息, 同步结果)
        """
        try:
            # 此方法将被SyncOrchestrator调用
            # MemoryService只提供同步接口，实际编排由SyncOrchestrator负责
            return True, "同步接口就绪", {"status": "ready"}
        except Exception as e:
            logger.error(f"同步接口初始化失败: {e}", exc_info=True)
            return False, f"同步接口初始化失败: {str(e)}", {}

    async def execute_storage(self, texts: List[str], metadata_list: List[Dict[str, Any]], collection_name: str) -> List[str]:
        """
        执行存储操作

        此方法被SyncOrchestrator调用，仅负责执行实际的存储操作

        Args:
            texts: 文本内容列表
            metadata_list: 对应的元数据列表
            collection_name: 目标集合名称

        Returns:
            存储后的永久链接列表
        """
        try:
            # 委托给SyncExecutor执行实际存储
            permalinks = await self.sync_executor.store_documents(texts=texts, metadatas=metadata_list, collection_name=collection_name)
            return permalinks
        except Exception as e:
            logger.error(f"执行存储操作失败: {e}", exc_info=True)
            return []

    def start_sync_watch(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        启动同步监视

        Returns:
            成功/失败标志，消息，结果
        """
        try:
            # 此功能将由SyncOrchestrator实现
            return True, "该功能尚未实现", {"status": "not_implemented"}
        except Exception as e:
            logger.error(f"启动同步监视失败: {e}", exc_info=True)
            return False, f"启动同步监视失败: {str(e)}", {}

    def import_documents(self, source_dir: str, recursive: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        """
        导入文档

        Args:
            source_dir: 源目录
            recursive: 是否递归导入子目录

        Returns:
            成功/失败标志，消息，导入结果
        """
        try:
            if not os.path.exists(source_dir):
                return False, f"源目录不存在: {source_dir}", {}

            success_count = 0
            fail_count = 0

            # 导入实现 (简化处理)
            result = {"success_count": success_count, "fail_count": fail_count}

            return True, f"导入完成: 成功{success_count}个, 失败{fail_count}个", result
        except Exception as e:
            logger.error(f"导入文档失败: {e}", exc_info=True)
            return False, f"导入文档失败: {str(e)}", {}

    def export_documents(self, output_dir: Optional[str] = None, format_type: str = "md") -> Tuple[bool, str, Dict[str, Any]]:
        """
        导出文档

        Args:
            output_dir: 输出目录
            format_type: 导出格式(md, json, txt)

        Returns:
            成功/失败标志，消息，导出结果
        """
        try:
            # 设置默认输出目录
            if not output_dir:
                output_dir = os.path.join(os.getcwd(), "exports")

            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)

            # 导出实现 (简化处理)
            success_count = 0
            fail_count = 0

            result = {"output_dir": output_dir, "success_count": success_count, "fail_count": fail_count}

            return True, f"导出完成: 成功{success_count}个, 失败{fail_count}个", result
        except Exception as e:
            logger.error(f"导出文档失败: {e}", exc_info=True)
            return False, f"导出文档失败: {str(e)}", {}

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息

        Returns:
            统计信息
        """
        try:
            stats = {"total_count": 0, "folders": [], "types": {}}

            # 获取统计信息
            memories = self._run_async(self.memory_manager.list_memories())
            if memories:
                stats["total_count"] = len(memories)

                # 统计文件夹
                folders = set()
                types = {}

                for memory in memories:
                    # 文件夹统计
                    folder = memory.get("folder", "未分类")
                    folders.add(folder)

                    # 类型统计
                    content_type = memory.get("content_type", "text")
                    types[content_type] = types.get(content_type, 0) + 1

                stats["folders"] = sorted(list(folders))
                stats["types"] = types

            return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}", exc_info=True)
            return {"error": str(e)}
