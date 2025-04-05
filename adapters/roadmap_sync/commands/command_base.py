"""
路线图命令基类

为所有路线图命令提供统一接口。
"""

import argparse
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from scripts.github_roadmap.github_sync import GitHubSync
from scripts.github_roadmap.roadmap_processor import RoadmapProcessor


class CommandBase(ABC):
    """命令基类，所有具体命令都应继承此类"""

    def __init__(self, processor: RoadmapProcessor, github_sync: Optional[GitHubSync] = None):
        """
        初始化命令

        Args:
            processor: 路线图处理器
            github_sync: GitHub同步工具，可选
        """
        self.processor = processor
        self.github_sync = github_sync
        self.name = self.__class__.__name__.lower().replace("command", "")

    @abstractmethod
    def add_parser(self, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        添加命令特定的参数解析器

        Args:
            subparsers: 子解析器集合

        Returns:
            argparse.ArgumentParser: 添加的解析器
        """
        pass

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        执行命令

        Args:
            args: 解析后的命令行参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        pass
