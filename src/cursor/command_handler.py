"""
Cursor命令处理器模块

负责：
- 处理Cursor IDE命令
- 集成规则系统
- 管理IDE交互
"""

import logging
from typing import Any, Dict

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
            command: 命令字符串

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 首先尝试使用规则引擎处理
            rule_result = self.rule_engine.process_command(command)
            if rule_result.get("handled", False):
                return rule_result

            # 如果规则引擎未处理，使用命令解析器
            return self.command_parser.execute_command(command)

        except Exception as e:
            error_msg = f"处理命令失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
