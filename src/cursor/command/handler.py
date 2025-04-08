"""
命令处理器模块

实现主要的命令处理逻辑
"""

import logging
from typing import Any, Dict, List, Tuple

from src.cli.command_parser import CommandParser
from src.cursor.command.formatter import enhance_result_for_agent
from src.cursor.command.suggestions import get_command_suggestions, get_error_suggestions, get_verbose_error_info
from src.rule_engine.core.rule_manager import RuleManager

logger = logging.getLogger(__name__)


class CursorCommandHandler:
    """Cursor命令处理器类"""

    def __init__(self):
        """初始化命令处理器"""
        self.command_parser = CommandParser()
        self.rule_engine = RuleManager()
        self._register_handlers()

    def _register_handlers(self):
        """注册命令处理器
        注意：命令处理器现在通过CommandParser自动注册
        """
        pass

    def handle_command(self, command: str) -> Dict[str, Any]:
        """处理命令

        Args:
            command: The command string like "/check --type=task --id=T2.1"

        Returns:
            Dict[str, Any]: Processing result with structured feedback for AI agent
        """
        logger.info(f"收到命令: {command}")

        try:
            # 解析命令结构
            command_name, args = self._parse_command(command)
            logger.debug(f"解析结果 - 命令: {command_name}, 参数: {args}")

            # 使用命令解析器执行命令
            result = self.command_parser.execute_command(command_name, args)
            logger.info(f"命令执行结果: {result}")

            # 增强AI友好的结果反馈
            return enhance_result_for_agent(result)

        except ValueError as ve:
            error_msg = f"命令格式错误: {str(ve)}"
            logger.error(error_msg)
            # 返回结构化的错误信息，包含建议
            return {
                "success": False,
                "error": error_msg,
                "error_type": "ValueError",
                "suggestions": self._get_command_suggestions(command),
                "verbose": get_verbose_error_info(ve),
            }
        except Exception as e:
            error_msg = f"处理命令失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # 返回结构化的错误信息，包含建议和详细信息
            return {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__,
                "suggestions": get_error_suggestions(e),
                "verbose": get_verbose_error_info(e),
            }

    def _parse_command(self, command: str) -> Tuple[str, List[str]]:
        """解析命令字符串为命令名和参数列表

        Args:
            command: 命令字符串，例如 "/check --type=task --id=T2.1"

        Returns:
            Tuple[str, List[str]]: 命令名和参数列表
        """
        if not command:
            raise ValueError("命令为空")

        # 移除前导斜杠和空格
        command = command.strip()
        if command.startswith("/"):
            command = command[1:]

        # 分割命令和参数
        parts = command.split()
        if not parts:
            raise ValueError("命令格式无效")

        command_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        return command_name, args

    def _get_command_suggestions(self, command: str) -> List[str]:
        """获取命令建议

        从当前可用命令中获取建议

        Args:
            command: 命令字符串

        Returns:
            List[str]: 建议列表
        """
        available_commands = self.get_available_commands()
        return get_command_suggestions(command, available_commands)

    def get_available_commands(self) -> List[Dict[str, Any]]:
        """获取可用命令列表

        Returns:
            List[Dict[str, Any]]: 可用命令列表
        """
        # 从命令解析器获取所有注册的命令
        commands = self.command_parser.get_available_commands()

        # 这里不再获取规则引擎的命令
        return commands

    def get_command_help(self, command_name: str) -> Dict[str, Any]:
        """获取命令帮助信息

        Args:
            command_name: 命令名称

        Returns:
            Dict[str, Any]: 帮助信息
        """
        available_commands = self.get_available_commands()
        command_info = next((cmd for cmd in available_commands if cmd["name"] == command_name), None)

        if not command_info:
            return {
                "success": False,
                "error": f"未知命令: {command_name}",
                "suggestions": ["使用 '/help' 查看所有可用命令", "检查命令名称是否正确"],
            }

        return {
            "success": True,
            "command": command_info["name"],
            "description": command_info["description"],
            "handler": command_info["handler"],
        }
