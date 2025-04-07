"""
Cursor命令系统包

提供命令处理和响应功能
"""

from src.cursor.command.formatter import (
    enhance_result_for_agent,
    generate_progress_bar,
    generate_summary,
)
from src.cursor.command.handler import CursorCommandHandler
from src.cursor.command.suggestions import (
    get_command_suggestions,
    get_error_suggestions,
    get_error_suggestions_from_message,
    get_similar_commands,
)

__all__ = [
    "CursorCommandHandler",
    "get_command_suggestions",
    "get_similar_commands",
    "get_error_suggestions",
    "get_error_suggestions_from_message",
    "enhance_result_for_agent",
    "generate_progress_bar",
    "generate_summary",
]
