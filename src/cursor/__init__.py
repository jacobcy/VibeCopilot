"""
VibeCopilot Cursor IDE 集成模块

包含：
- Cursor命令处理
- 规则集成
- IDE交互
"""

__version__ = "0.1.0"

from .command_handler import CursorCommandHandler

__all__ = ["CursorCommandHandler"]
