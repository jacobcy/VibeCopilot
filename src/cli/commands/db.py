"""
数据库命令处理模块

提供数据库管理操作的命令接口，集成数据库服务功能。
此文件为兼容性封装，实际实现已移至db包。
"""

from src.cli.commands.db import DatabaseCommand

# 保留原有命令类以保证向后兼容
__all__ = ["DatabaseCommand"]
