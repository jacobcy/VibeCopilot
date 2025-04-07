#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令解析器

负责解析命令行参数，识别命令名称和参数
"""

import sys
from typing import Any, Dict, List, Optional, Tuple

from src.cli.commands import COMMAND_REGISTRY


class CommandParser:
    """命令解析器"""

    def __init__(self):
        """初始化命令解析器"""
        self.commands = COMMAND_REGISTRY

    def parse_command(self) -> Tuple[str, List[str]]:
        """
        解析命令行参数

        Returns:
            (命令名称, 命令参数)
        """
        # 获取命令行参数（跳过脚本名称）
        args = sys.argv[1:]

        # 如果没有参数，默认为help命令
        if not args:
            return "help", []

        # 获取命令名称
        command_name = args.pop(0)

        # 返回命令名称和剩余参数
        return command_name, args

    def execute_command(self, command_name: str, args: List[str]) -> Dict[str, Any]:
        """执行命令

        Args:
            command_name: 命令名称
            args: 命令参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        if command_name not in self.commands:
            raise ValueError(f"未知命令: {command_name}")

        command_handler = self.commands[command_name]
        return command_handler(args)

    def get_available_commands(self) -> List[Dict[str, Any]]:
        """获取可用命令列表

        Returns:
            List[Dict[str, Any]]: 可用命令列表
        """
        commands = []
        for name, handler in self.commands.items():
            commands.append({"name": name, "description": handler.__doc__ or "无描述", "handler": handler.__name__})
        return commands
