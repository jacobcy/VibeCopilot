"""
命令解析器模块

负责：
- 命令解析
- 参数验证
- 命令路由
"""

import logging
import re
from typing import Any, Dict, Tuple

from src.cli.base_command import BaseCommand
from src.cli.commands.check_command import CheckCommand
from src.cli.commands.update_command import UpdateCommand

logger = logging.getLogger(__name__)


class CommandParser:
    """命令解析器类"""

    def __init__(self):
        """初始化命令解析器"""
        self.commands = {}
        self._register_default_commands()

    def _register_default_commands(self):
        """注册默认命令"""
        self.register_command(CheckCommand())
        self.register_command(UpdateCommand())

    def parse_command(self, command_str: str) -> Tuple[str, Dict[str, Any]]:
        """解析命令字符串

        Args:
            command_str: 要解析的命令字符串

        Returns:
            Tuple[str, Dict[str, Any]]: 命令名称和参数字典

        Raises:
            ValueError: 命令格式无效
        """
        if not command_str:
            raise ValueError("命令不能为空")

        if not command_str.startswith("/"):
            raise ValueError("命令必须以/开头")

        # 移除开头的斜杠并分割命令和参数
        parts = command_str[1:].split(" ")
        command_name = parts[0]
        args = {}

        # 解析参数
        for part in parts[1:]:
            if part.startswith("--"):
                if "=" in part:
                    key, value = part[2:].split("=", 1)
                    args[key] = value
                else:
                    key = part[2:]
                    args[key] = True

        return command_name, args

    def register_command(self, command):
        """注册命令处理器"""
        self.commands[command.name] = command

    def execute_command(self, command_str: str) -> Dict[str, Any]:
        """执行命令

        Args:
            command_str: 要执行的命令字符串

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            command_name, args = self.parse_command(command_str)

            if command_name not in self.commands:
                return {"success": False, "error": f"未知命令: {command_name}"}

            return self.commands[command_name].execute(args)

        except ValueError as e:
            error_msg = f"处理命令失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"执行命令失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
