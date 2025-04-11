"""
路线图新版命令入口点

提供一个临时的导入点，用于测试新版的roadmap命令而不影响原来的代码。
"""

from src.cli.commands.roadmap_new.roadmap_click import roadmap as roadmap_new

# 导出命令
__all__ = ["roadmap_new"]
