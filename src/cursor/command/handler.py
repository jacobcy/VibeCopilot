"""
命令处理器模块

实现主要的命令处理逻辑
"""

import logging
from typing import Any, Dict, List, Tuple

from src.cli.command_parser import CommandParser
from src.core.rule_engine import RuleEngine
from src.cursor.command.formatter import enhance_result_for_agent
from src.cursor.command.suggestions import (
    get_command_suggestions,
    get_error_suggestions,
    get_verbose_error_info,
)

logger = logging.getLogger(__name__)


class CursorCommandHandler:
    """Cursor命令处理器类"""

    def __init__(self):
        """初始化命令处理器"""
        self.command_parser = CommandParser()
        self.rule_engine = RuleEngine()
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
            # 首先尝试使用规则引擎处理
            rule_result = self.rule_engine.process_command(command)
            if rule_result.get("handled", False):
                logger.info(f"规则引擎处理结果: {rule_result}")
                # 增强AI友好的结果反馈
                return enhance_result_for_agent(rule_result)

            # 如果规则引擎未处理，解析命令结构
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
                "verbose": self._get_verbose_error_info(ve),
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
                "verbose": self._get_verbose_error_info(e),
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

        # 添加规则引擎的命令
        rule_commands = self.rule_engine.get_available_commands()
        commands.extend(rule_commands)

        return commands

    def _get_verbose_error_info(self, error: Exception) -> Dict[str, Any]:
        """获取详细错误信息

        Args:
            error: 异常对象

        Returns:
            Dict[str, Any]: 详细错误信息
        """
        error_type = type(error).__name__
        error_msg = str(error)
        error_info = {
            "error_type": error_type,
            "error_message": error_msg,
            "context": "命令处理器",
        }

        # 添加异常详细信息
        if hasattr(error, "__dict__"):
            # 过滤掉内置属性
            error_attrs = {
                k: v
                for k, v in error.__dict__.items()
                if not k.startswith("__") and not k.endswith("__")
            }
            if error_attrs:
                error_info["error_details"] = error_attrs

        return error_info
