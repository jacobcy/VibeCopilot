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

# Expose the main service facade
from .memory_service import MemoryService, get_memory_service

# Expose operations if needed directly (usually accessed via MemoryService)
# from .memory_operations import ...

__all__ = ["MemoryService", "get_memory_service"]
