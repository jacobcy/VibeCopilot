#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令基类模块

提供命令的基础功能和接口定义
"""

import argparse
import logging
from typing import Any, List, Optional

from src.cli.command import Command

logger = logging.getLogger(__name__)


class BaseCommand(Command):
    """命令基类，实现基本的命令行解析和执行流程"""

    def __init__(self, name: str, description: str):
        """
        初始化命令基类

        Args:
            name: 命令名称
            description: 命令描述
        """
        self.name = name
        self.description = description

    def parse_args(self, args: List[str]) -> argparse.Namespace:
        """
        解析命令行参数

        Args:
            args: 命令行参数列表

        Returns:
            解析后的参数对象
        """
        parser = argparse.ArgumentParser(
            prog=f"vibecopilot {self.name}", description=self.description
        )

        # 让子类配置解析器
        self.configure_parser(parser)

        # 解析参数
        return parser.parse_args(args)

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        配置命令行解析器，由子类实现

        Args:
            parser: 命令行解析器
        """
        pass

    def execute(self, args: List[str]) -> int:
        """
        执行命令

        Args:
            args: 命令行参数列表

        Returns:
            命令执行结果状态码
        """
        # 解析参数
        parsed_args = self.parse_args(args)

        # 调用具体实现
        return self.execute_with_args(parsed_args)

    def execute_with_args(self, args: argparse.Namespace) -> int:
        """
        执行命令，使用解析后的参数，由子类实现

        Args:
            args: 解析后的参数对象

        Returns:
            命令执行结果状态码
        """
        logger.warning(f"{self.name} 命令未实现执行逻辑")
        return 1
