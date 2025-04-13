"""
任务管理命令模块

提供任务管理相关的命令实现，包括创建、查询、更新和删除操作。
"""

# 导入Click版本的task命令组
from .task_click import task

# 导出Click命令组，供主程序使用
__all__ = ["task"]
