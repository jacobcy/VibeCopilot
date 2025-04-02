"""
Cursor命令处理模块

负责：
- 处理Cursor IDE命令
- 集成规则系统
- 管理IDE交互
"""

import logging
from typing import Dict, Optional

from src.cli.command_parser import CommandParser
from src.core.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


class CursorCommandHandler:
    """Cursor命令处理器核心类"""

    def __init__(self):
        self.command_parser = CommandParser()
        self.rule_engine = RuleEngine()

    def handle_command(self, command_str: str) -> Dict:
        """处理Cursor命令"""
        try:
            # 首先通过规则引擎处理
            rule_result = self.rule_engine.process_command(command_str)
            if rule_result.get("handled", False):
                return rule_result

            # 如果规则引擎没有处理，则通过命令解析器处理
            return self.command_parser.execute_command(command_str)

        except Exception as e:
            logger.error(f"处理命令失败: {e}")
            return {"success": False, "error": f"处理命令失败: {e}"}

    def register_handlers(self) -> None:
        """注册命令处理器"""
        # 命令处理器现在通过CommandParser自动注册
        pass
