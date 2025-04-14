"""
任务命令包

提供基于Click的任务管理命令实现
"""

from .base_command import BaseCommand

# 注意：以下类已经转换为纯Click命令函数
# - CreateTaskCommand 改为 create_task
# - ListTaskCommand 改为 list_tasks
# - ShowTaskCommand 改为 show_task
# - UpdateTaskCommand 改为 update_task
# - CommentTaskCommand 改为 comment_task
# - DeleteTaskCommand 改为 delete_task
# - LinkTaskCommand 改为 link_task

__all__ = [
    "BaseCommand",
]
