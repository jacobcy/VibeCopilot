#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一内存服务模块

提供对知识库功能的统一访问接口，整合笔记管理、搜索和同步功能。
作为NoteService、SearchService和SyncService的门面(Facade)，
向外部提供简洁统一的API，隐藏内部实现细节。
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from src.memory.services.note_service import NoteService
from src.memory.services.search_service import SearchService
from src.memory.services.sync_service import SyncService

logger = logging.getLogger(__name__)


class MemoryService:
    """统一内存服务类

    作为门面(Facade)模式实现，整合多个子服务的功能，
    提供统一的接口给CLI层和外部系统使用。
    """

    def __init__(self):
        """初始化统一内存服务"""
        self.note_service = NoteService()
        self.search_service = SearchService()
        self.sync_service = SyncService()
        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化统一内存服务")

    # ===== 笔记管理功能 =====

    def create_note(self, content: str, title: str, folder: str, tags: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """创建新笔记

        Args:
            content: 笔记内容
            title: 笔记标题
            folder: 存储目录
            tags: 标签列表，逗号分隔

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        return self.note_service.create_note(content=content, title=title, folder=folder, tags=tags)

    def read_note(self, path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """读取笔记内容

        Args:
            path: 笔记路径或永久链接

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        return self.note_service.read_note(path=path)

    def update_note(self, path: str, content: str, tags: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """更新笔记内容

        Args:
            path: 笔记路径或永久链接
            content: 更新后的内容
            tags: 更新的标签，逗号分隔

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        return self.note_service.update_note(path=path, content=content, tags=tags)

    def delete_note(self, path: str, force: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        """删除笔记

        Args:
            path: 笔记路径或永久链接
            force: 是否强制删除

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        return self.note_service.delete_note(path=path, force=force)

    # ===== 搜索功能 =====

    def list_notes(self, folder: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """列出知识库笔记

        Args:
            folder: 筛选特定目录的内容

        Returns:
            元组，包含(是否成功, 消息, 结果列表)
        """
        return self.search_service.list_notes(folder=folder)

    def search_notes(self, query: str, content_type: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """搜索知识库内容

        Args:
            query: 搜索关键词
            content_type: 内容类型过滤

        Returns:
            元组，包含(是否成功, 消息, 结果列表)
        """
        return self.search_service.search_notes(query=query, content_type=content_type)

    # ===== 同步功能 =====

    def sync_all(self) -> Tuple[bool, str, Dict[str, Any]]:
        """同步所有知识库内容

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        return self.sync_service.sync_all()

    def start_sync_watch(self) -> Tuple[bool, str, Dict[str, Any]]:
        """启动知识库监控

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        return self.sync_service.start_sync_watch()

    def import_documents(self, source_dir: str, recursive: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        """从外部导入文档

        Args:
            source_dir: 源文档目录
            recursive: 是否递归导入子目录

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        return self.sync_service.import_documents(source_dir=source_dir, recursive=recursive)

    def export_documents(self, output_dir: Optional[str] = None, format_type: str = "md") -> Tuple[bool, str, Dict[str, Any]]:
        """导出知识库文档

        Args:
            output_dir: 输出目录
            format_type: 导出格式，支持md和json

        Returns:
            元组，包含(是否成功, 消息, 结果数据)
        """
        return self.sync_service.export_documents(output_dir=output_dir, format_type=format_type)

    # ===== 统计与状态 =====

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息

        Returns:
            字典，包含知识库统计数据
        """
        # 结合不同服务的统计信息
        note_stats = self.note_service.get_stats()
        sync_stats = self.sync_service.get_sync_status()

        # 合并统计结果
        stats = {**note_stats, "sync_status": sync_stats}

        return stats
