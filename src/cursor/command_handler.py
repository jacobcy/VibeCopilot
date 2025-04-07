"""
Cursor命令处理器模块

负责：
- 处理Cursor IDE命令
- 集成规则系统
- 管理IDE交互
"""

import logging
from typing import Any, Dict

from src.cursor.command import CursorCommandHandler

logger = logging.getLogger(__name__)

# 创建命令处理器单例
_command_handler = None


def get_command_handler() -> CursorCommandHandler:
    """获取命令处理器单例

    Returns:
        CursorCommandHandler: 命令处理器实例
    """
    global _command_handler
    if _command_handler is None:
        _command_handler = CursorCommandHandler()
    return _command_handler


def handle_command(command: str) -> Dict[str, Any]:
    """处理命令

    Args:
        command: 命令字符串，例如 "/check --type=task --id=T2.1"

    Returns:
        Dict[str, Any]: 处理结果
    """
    handler = get_command_handler()
    return handler.handle_command(command)
