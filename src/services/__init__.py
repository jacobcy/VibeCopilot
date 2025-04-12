"""
服务层模块

提供业务逻辑服务，连接命令层和数据访问层。
"""

from .task_service import TaskService

__all__ = [
    "TaskService",
]
