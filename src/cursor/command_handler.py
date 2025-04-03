"""
Cursor命令处理器模块

负责：
- 处理Cursor IDE命令
- 集成规则系统
- 管理IDE交互
"""

import logging
from typing import Any, Dict, List, Tuple

from src.cli.command_parser import CommandParser
from src.core.rule_engine import RuleEngine

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
            command: 命令字符串，如 "/check --type=task --id=T2.1"

        Returns:
            Dict[str, Any]: 处理结果
        """
        logger.info(f"收到命令: {command}")

        try:
            # 首先尝试使用规则引擎处理
            rule_result = self.rule_engine.process_command(command)
            if rule_result.get("handled", False):
                logger.info(f"规则引擎处理结果: {rule_result}")
                return rule_result

            # 如果规则引擎未处理，解析命令结构
            command_name, args = self._parse_command(command)
            logger.debug(f"解析结果 - 命令: {command_name}, 参数: {args}")

            # 使用命令解析器执行命令
            result = self.command_parser.execute_command(command_name, args)
            logger.info(f"命令执行结果: {result}")
            return result

        except ValueError as ve:
            error_msg = f"命令格式错误: {str(ve)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"处理命令失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg, "error_type": type(e).__name__}

    def _parse_command(self, command_str: str) -> Tuple[str, Dict[str, Any]]:
        """解析命令字符串，返回命令名称和参数字典

        Args:
            command_str: 命令字符串，如 "/check --type=task --id=T2.1"

        Returns:
            Tuple[str, Dict[str, Any]]: 命令名称和参数字典
        """
        if not command_str.startswith("/"):
            raise ValueError("命令必须以'/'开头")

        parts = command_str[1:].strip().split()
        if not parts:
            raise ValueError("无效的命令格式")

        command_name = parts[0]
        args = {}

        # 解析参数
        for part in parts[1:]:
            if part.startswith("--"):
                if "=" in part:
                    key, value = part[2:].split("=", 1)
                    args[key] = self._convert_arg_value(value)
                else:
                    args[part[2:]] = True
            elif "=" in part and not part.startswith("-"):
                # 支持不带--前缀的key=value格式
                key, value = part.split("=", 1)
                args[key] = self._convert_arg_value(value)

        return command_name, args

    def _convert_arg_value(self, value: str) -> Any:
        """尝试将参数值转换为适当的类型

        Args:
            value: 参数值字符串

        Returns:
            转换后的参数值
        """
        # 尝试转换为布尔值
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # 尝试转换为整数
        try:
            return int(value)
        except ValueError:
            pass

        # 尝试转换为浮点数
        try:
            return float(value)
        except ValueError:
            pass

        # 保持字符串类型
        return value

    def get_available_commands(self) -> List[Dict[str, str]]:
        """获取所有可用命令的列表

        Returns:
            List[Dict[str, str]]: 可用命令列表，每个命令包含名称和描述
        """
        return self.command_parser.get_available_commands()

    def get_command_help(self, command_name: str) -> Dict[str, Any]:
        """获取指定命令的帮助信息

        Args:
            command_name: 命令名称

        Returns:
            Dict[str, Any]: 命令帮助信息
        """
        return self.command_parser.get_command_help(command_name)
