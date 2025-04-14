"""
任务服务模块

提供任务相关的服务层接口，整合数据访问和业务逻辑。
"""

from src.services.task.core import TaskService

__all__ = [
    "TaskService",
]
