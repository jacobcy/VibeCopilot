"""
知识库命令模块

提供管理VibeCopilot知识库的命令。
"""

from src.cli.commands.memory.memory_click import memory as memory_click_group

__all__ = ["memory_click_group"]
