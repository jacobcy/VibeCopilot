#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VibeCopilot 记忆服务模块

提供对Basic Memory和本地存储的统一管理，包括：
- 笔记服务：管理Basic Memory中的笔记
- 搜索服务：提供对Basic Memory内容的搜索能力
- 同步服务：执行各种同步操作，包括导入/导出
- 记忆项服务：管理本地数据库中的记忆项并与Basic Memory同步
"""

from .memory_item_service import MemoryItemService
from .note_service import NoteService
from .search_service import SearchService
from .sync_service import SyncService

__all__ = ["NoteService", "SearchService", "SyncService", "MemoryItemService"]
