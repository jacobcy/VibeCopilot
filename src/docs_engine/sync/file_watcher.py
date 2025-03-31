"""
文件监控工具 - 监控文档变更并触发同步.

使用watchdog库实现对文档目录的实时监控，检测文件变更并触发同步操作.
"""

import logging
import os
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer


class DocFileHandler(FileSystemEventHandler):
    """文档文件变更处理器."""

    def __init__(
        self,
        base_dir: str,
        callback: Callable[[str, str], None],
        exclude_patterns: List[str] = None,
    ):
        """
        初始化文件处理器.

        Args:
            base_dir: 基准目录
            callback: 变更回调函数(接收相对路径和事件类型)
            exclude_patterns: 要排除的文件模式
        """
        self.base_dir = Path(base_dir)
        self.callback = callback
        self.exclude_patterns = exclude_patterns or []
        self.logger = logging.getLogger("doc_file_handler")

        # 延迟处理缓冲，避免频繁触发同一文件的多个事件
        self.pending_events = {}
        self.debounce_seconds = 1.0

    def on_any_event(self, event: FileSystemEvent):
        """
        处理所有文件系统事件.

        Args:
            event: 文件系统事件
        """
        if event.is_directory:
            return

        # 获取相对路径
        try:
            src_path = Path(event.src_path)
            rel_path = src_path.relative_to(self.base_dir)
            rel_path_str = str(rel_path)
        except (ValueError, AttributeError):
            return

        # 检查是否应该忽略
        if self._should_ignore(rel_path_str):
            return

        # 确定事件类型
        event_type = "unknown"
        if isinstance(event, FileCreatedEvent):
            event_type = "created"
        elif isinstance(event, FileModifiedEvent):
            event_type = "modified"
        elif isinstance(event, FileDeletedEvent):
            event_type = "deleted"

        # 只处理Markdown文件
        if event_type != "deleted" and not self._is_markdown_file(rel_path_str):
            return

        # 将事件添加到延迟处理缓冲
        self.pending_events[rel_path_str] = (event_type, time.time())

        # 启动延迟处理
        self._process_pending_events()

    def _should_ignore(self, rel_path: str) -> bool:
        """
        检查文件是否应该被忽略.

        Args:
            rel_path: 相对文件路径

        Returns:
            是否应该忽略该文件
        """
        from fnmatch import fnmatch

        # 检查排除模式
        for pattern in self.exclude_patterns:
            if fnmatch(rel_path, pattern):
                return True

        return False

    def _is_markdown_file(self, file_path: str) -> bool:
        """
        检查文件是否为Markdown文件.

        Args:
            file_path: 文件路径

        Returns:
            是否为Markdown文件
        """
        extensions = [".md", ".mdx", ".markdown"]
        return any(file_path.lower().endswith(ext) for ext in extensions)

    def _process_pending_events(self):
        """处理挂起的文件事件，应用防抖动逻辑."""
        current_time = time.time()
        processed = set()

        for rel_path, (event_type, timestamp) in list(self.pending_events.items()):
            # 检查事件是否已经足够"老"可以处理
            if current_time - timestamp >= self.debounce_seconds:
                try:
                    self.callback(rel_path, event_type)
                except Exception as e:
                    self.logger.error(f"处理文件事件失败: {rel_path} - {str(e)}")

                processed.add(rel_path)

        # 从挂起事件中移除已处理的事件
        for rel_path in processed:
            self.pending_events.pop(rel_path, None)


class FileWatcher:
    """文档文件监控器，监控文件变更并触发同步."""

    def __init__(
        self,
        watch_dir: str,
        sync_callback: Callable[[str, str], None],
        exclude_patterns: List[str] = None,
    ):
        """
        初始化文件监控器.

        Args:
            watch_dir: 要监控的目录
            sync_callback: 同步回调函数(接收相对路径和事件类型)
            exclude_patterns: 要排除的文件模式
        """
        self.watch_dir = Path(watch_dir)
        self.sync_callback = sync_callback
        self.exclude_patterns = exclude_patterns or []

        self.event_handler = DocFileHandler(watch_dir, sync_callback, exclude_patterns)
        self.observer = Observer()

        # 设置logger
        self.logger = logging.getLogger("file_watcher")

    def start(self):
        """启动文件监控."""
        self.observer.schedule(self.event_handler, str(self.watch_dir), recursive=True)
        self.observer.start()
        self.logger.info(f"开始监控目录: {self.watch_dir}")

    def stop(self):
        """停止文件监控."""
        self.observer.stop()
        self.observer.join()
        self.logger.info("停止监控目录")

    def is_running(self) -> bool:
        """
        检查监控器是否正在运行.

        Returns:
            是否正在运行
        """
        return self.observer.is_alive()
