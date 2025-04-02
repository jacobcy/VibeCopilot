"""
命令解析器模块

负责：
- 命令解析
- 参数验证
- 命令路由
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Type

from src.cli.base_command import BaseCommand
from src.cli.commands.check_command import CheckCommand
from src.cli.commands.update_command import UpdateCommand

logger = logging.getLogger(__name__)


class CommandParser:
    """命令解析器核心类"""

    def __init__(self):
        self.commands: Dict[str, BaseCommand] = {}
        self._register_default_commands()

    def _register_default_commands(self) -> None:
        """注册默认命令"""
        self.register_command(CheckCommand())
        self.register_command(UpdateCommand())

    def parse_command(self, command_str: str) -> Tuple[str, Dict]:
        """解析命令字符串，返回命令名和参数"""
        if not command_str.startswith("/"):
            raise ValueError("命令必须以/开头")

        # 移除开头的/并分割命令和参数
        parts = command_str[1:].split()
        if not parts:
            raise ValueError("命令不能为空")

        command_name = parts[0]
        args = self._parse_args(parts[1:])

        return command_name, args

    def _parse_args(self, args_list: List[str]) -> Dict:
        """解析参数列表为字典"""
        args = {}
        for arg in args_list:
            if arg.startswith("--"):
                key_value = arg[2:].split("=", 1)
                if len(key_value) == 2:
                    key, value = key_value
                    args[key] = value
                else:
                    args[key_value[0]] = True
        return args

    def register_command(self, command: BaseCommand) -> None:
        """注册命令处理器"""
        self.commands[command.name] = command

    def execute_command(self, command_str: str) -> Dict:
        """执行命令"""
        try:
            command_name, args = self.parse_command(command_str)

            if command_name not in self.commands:
                return {"success": False, "error": f"未知命令: {command_name}"}

            return self.commands[command_name].execute(args)

        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            return {"success": False, "error": f"执行命令失败: {e}"}
