"""
Obsidian适配器模块

提供与Obsidian知识库交互的功能，包括文件监控、同步和格式转换。
"""

from adapters.obsidian.sync.file_watcher import FileWatcher

__all__ = ["FileWatcher"]
