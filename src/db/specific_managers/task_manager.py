"""
Task管理器模块

提供Task实体的管理功能。
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskManager:
    """Task管理器

    提供Task实体的管理功能。
    """

    def __init__(self, entity_manager, task_repo):
        """初始化Task管理器

        Args:
            entity_manager: 实体管理器
            task_repo: Task仓库
        """
        self._entity_manager = entity_manager
        self._task_repo = task_repo

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """获取Task信息

        Args:
            task_id: Task ID

        Returns:
            Task信息
        """
        return self._entity_manager.get_entity("task", task_id)

    def list_tasks(self) -> List[Dict[str, Any]]:
        """获取所有Task

        Returns:
            Task列表
        """
        return self._entity_manager.get_entities("task")

    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Task

        Args:
            data: Task数据

        Returns:
            创建的Task
        """
        return self._entity_manager.create_entity("task", data)

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Task

        Args:
            task_id: Task ID
            data: 更新数据

        Returns:
            更新后的Task
        """
        return self._entity_manager.update_entity("task", task_id, data)

    def delete_task(self, task_id: str) -> bool:
        """删除Task

        Args:
            task_id: Task ID

        Returns:
            是否成功
        """
        return self._entity_manager.delete_entity("task", task_id)

    def get_tasks_by_status(self, status: str) -> List[Dict[str, Any]]:
        """根据状态获取Task

        Args:
            status: 状态

        Returns:
            Task列表
        """
        try:
            tasks = self._task_repo.get_by_status(status)
            return [task.to_dict() if hasattr(task, "to_dict") else vars(task) for task in tasks]
        except Exception as e:
            logger.error(f"获取状态为 {status} 的任务时出错: {e}")
            return []

    def get_tasks_by_assignee(self, assignee: str) -> List[Dict[str, Any]]:
        """根据分配人获取Task

        Args:
            assignee: 分配人

        Returns:
            Task列表
        """
        try:
            tasks = self._task_repo.get_by_assignee(assignee)
            return [task.to_dict() if hasattr(task, "to_dict") else vars(task) for task in tasks]
        except Exception as e:
            logger.error(f"获取分配给 {assignee} 的任务时出错: {e}")
            return []
