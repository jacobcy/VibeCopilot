#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令基类模块

提供命令的基础功能和接口定义
"""
import argparse
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.cli.command import Command

logger = logging.getLogger(__name__)
console = Console()


class BaseCommand(ABC):
    """命令基类"""

    def __init__(self, name: str, description: str):
        """初始化命令"""
        self.name = name
        self.description = description
        self._parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """创建命令行解析器"""
        parser = argparse.ArgumentParser(prog=self.name, description=self.description, formatter_class=argparse.RawDescriptionHelpFormatter)
        self.configure_parser(parser)
        return parser

    @abstractmethod
    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """配置命令行解析器"""
        pass

    @abstractmethod
    def execute_with_args(self, args: argparse.Namespace) -> int:
        """执行命令"""
        pass

    def execute(self, args: List[str]) -> int:
        """执行命令的入口点"""
        try:
            parsed_args = self._parser.parse_args(args)
            return self.execute_with_args(parsed_args)
        except Exception as e:
            console.print(f"[red]错误:[/red] {str(e)}")
            return 1

    def print_help(self) -> None:
        """打印帮助信息"""
        self._parser.print_help()

    @classmethod
    def get_help(cls) -> str:
        """获取命令的帮助信息"""
        # 如果子类有自己的文档字符串，就使用它
        if cls.__doc__:
            return cls.__doc__
        # 否则返回一个基本的帮助信息
        return "暂无帮助信息"
