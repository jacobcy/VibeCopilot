"""
命令处理器模块

实现主要的命令处理逻辑，使用Click框架
"""

import logging
import sys
from typing import Any, Dict, List, Tuple

import click
from rich.console import Console

from src.cli.commands import CLICK_COMMANDS, OLD_COMMANDS
from src.cli.main import get_cli_app
from src.cursor.command.formatter import enhance_result_for_agent
from src.cursor.command.suggestions import get_command_suggestions, get_error_suggestions, get_verbose_error_info
from src.rule_engine.core.rule_manager import RuleManager

logger = logging.getLogger(__name__)
console = Console()


class CursorCommandHandler:
    """Cursor命令处理器类"""

    def __init__(self):
        """初始化命令处理器"""
        self.cli = get_cli_app()
        self.rule_engine = RuleManager()

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

            # 使用Click框架执行命令
            result = self._execute_click_command(command_name, args)
            logger.info(f"命令执行结果: {result}")

            # 增强AI友好的结果反馈
            return enhance_result_for_agent(result)

        except click.exceptions.UsageError as ue:
            error_msg = f"命令用法错误: {str(ue)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "UsageError",
                "suggestions": self._get_command_suggestions(command),
                "verbose": get_verbose_error_info(ue),
            }
        except click.exceptions.ClickException as ce:
            error_msg = f"命令执行错误: {str(ce)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "ClickException",
                "suggestions": get_error_suggestions(ce),
                "verbose": get_verbose_error_info(ce),
            }
        except Exception as e:
            error_msg = f"处理命令失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
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

    def _execute_click_command(self, command_name: str, args: List[str]) -> Dict[str, Any]:
        """使用Click框架执行命令

        Args:
            command_name: 命令名称
            args: 命令参数列表

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 构建完整的命令参数列表
        full_args = [command_name] + args

        # 保存原始的sys.argv
        original_argv = sys.argv
        try:
            # 替换sys.argv为当前命令
            sys.argv = ["vibecopilot"] + full_args
            # 执行命令
            result = self.cli.main(standalone_mode=False)
            return {"success": True, "result": result}
        except click.exceptions.Exit as e:
            # 正常退出（比如显示帮助信息）
            return {"success": True, "result": None}
        finally:
            # 恢复原始的sys.argv
            sys.argv = original_argv

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
        commands = []

        # 添加Click命令
        for name, cmd in CLICK_COMMANDS.items():
            commands.append({"name": name, "description": cmd.help or "无描述", "handler": cmd.__name__})

        # 添加旧式命令（临时，直到完全迁移）
        for name, cmd_class in OLD_COMMANDS.items():
            commands.append(
                {"name": name, "description": cmd_class.get_help() if hasattr(cmd_class, "get_help") else "无描述", "handler": cmd_class.__name__}
            )

        return commands

    def get_command_help(self, command_name: str) -> Dict[str, Any]:
        """获取命令帮助信息

        Args:
            command_name: 命令名称

        Returns:
            Dict[str, Any]: 帮助信息
        """
        # 首先检查Click命令
        if command_name in CLICK_COMMANDS:
            cmd = CLICK_COMMANDS[command_name]
            return {"success": True, "command": command_name, "description": cmd.help or "无描述", "handler": cmd.__name__}

        # 然后检查旧式命令
        if command_name in OLD_COMMANDS:
            cmd_class = OLD_COMMANDS[command_name]
            return {
                "success": True,
                "command": command_name,
                "description": cmd_class.get_help() if hasattr(cmd_class, "get_help") else "无描述",
                "handler": cmd_class.__name__,
            }

        return {
            "success": False,
            "error": f"未知命令: {command_name}",
            "suggestions": ["使用 '/help' 查看所有可用命令", "检查命令名称是否正确"],
        }
