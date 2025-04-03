"""
命令解析器模块

负责：
- 命令解析
- 参数验证
- 命令路由
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.cli.base_command import BaseCommand
from src.cli.commands.blog import BlogCommand
from src.cli.commands.check import CheckCommand
from src.cli.commands.github import GitHubCommand
from src.cli.commands.update import UpdateCommand

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
        self.register_command(GitHubCommand())
        self.register_command(BlogCommand())
        # 注册其他命令...

    def parse_command(self, command_str: str) -> Tuple[str, Dict[str, Any]]:
        """解析命令字符串 (原始解析方法，保留以支持向后兼容)

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

    def register_command(self, command: BaseCommand):
        """注册命令处理器

        Args:
            command: 命令处理器实例
        """
        self.commands[command.name] = command
        logger.info(f"已注册命令: {command.name}")

    def execute_command(self, command_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行命令

        Args:
            command_name: 命令名称
            args: 命令参数

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            if command_name not in self.commands:
                return {"success": False, "error": f"未知命令: {command_name}"}

            # 获取命令处理器并执行
            command_handler = self.commands[command_name]
            logger.debug(f"执行命令: {command_name}, 参数: {args}")
            return command_handler.execute(args)

        except Exception as e:
            error_msg = f"执行命令失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg, "error_type": type(e).__name__}

    def get_available_commands(self) -> List[Dict[str, str]]:
        """获取所有可用命令的列表

        Returns:
            List[Dict[str, str]]: 命令列表，包含名称和描述
        """
        return [
            {"name": name, "description": cmd.description} for name, cmd in self.commands.items()
        ]

    def get_command_help(self, command_name: str) -> Dict[str, Any]:
        """获取指定命令的帮助信息

        Args:
            command_name: 命令名称

        Returns:
            Dict[str, Any]: 命令帮助信息
        """
        if command_name not in self.commands:
            return {"success": False, "error": f"未知命令: {command_name}"}

        command = self.commands[command_name]
        return {
            "success": True,
            "command": command_name,
            "description": command.description,
            "usage": command.get_usage(),
            "examples": command.get_examples(),
        }

    # 保留原有execute_command方法的向后兼容性实现
    def execute_command_string(self, command_str: str) -> Dict[str, Any]:
        """执行命令字符串（向后兼容方法）

        Args:
            command_str: 要执行的命令字符串

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            command_name, args = self.parse_command(command_str)
            return self.execute_command(command_name, args)
        except ValueError as e:
            error_msg = f"处理命令失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"执行命令失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg}
