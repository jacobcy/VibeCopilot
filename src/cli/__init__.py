"""
CLI命令行包

提供VibeCopilot命令行交互功能
"""

from src.cli.base_command import BaseCommand
from src.cli.main import main

__all__ = [
    "BaseCommand",  # 基础命令类
    "main",  # CLI主入口函数
]
