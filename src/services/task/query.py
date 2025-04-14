"""
任务查询服务模块

提供任务的查询、过滤等功能。
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskQueryService:
    """任务查询服务类，负责任务的查询和过滤操作"""

    def __init__(self, db_service):
        """初始化任务查询服务

        Args:
            db_service: 数据库服务实例
        """
        self._db_service = db_service

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """获取当前任务"""
        try:
            task = self._db_service.task_repo.get_current_task()
            return task.to_dict() if task else None
        except Exception as e:
            logger.error(f"获取当前任务失败: {e}")
            return None

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典，如果找不到则返回None
        """
        try:
            return self._db_service.get_task(task_id)
        except Exception as e:
            logger.error(f"获取任务 {task_id} 失败: {e}")
            return None

    def list_tasks(
        self,
        status: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        story_id: Optional[str] = None,
        is_independent: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """获取任务列表，支持多种过滤条件

        Args:
            status: 按状态过滤
            assignee: 按负责人过滤
            labels: 按标签过滤
            story_id: 按关联的Story ID过滤
            is_independent: 是否只返回独立任务
            limit: 返回结果数量限制
            offset: 结果偏移量

        Returns:
            任务列表
        """
        try:
            # 注意：实际实现需要根据DatabaseService的能力来调整
            # 这里简化处理，假设DatabaseService有类似的方法
            tasks = self._db_service.list_tasks()

            # 简单的筛选逻辑，实际中可能需要更复杂的实现或直接由数据库层处理
            filtered_tasks = []
            for task in tasks:
                # 状态过滤
                if status and task.get("status") not in status:
                    continue

                # 负责人过滤
                if assignee and task.get("assignee") != assignee:
                    continue

                # 标签过滤
                if labels:
                    task_labels = task.get("labels", [])
                    if not any(label in task_labels for label in labels):
                        continue

                # 关联Story过滤
                if story_id and task.get("story_id") != story_id:
                    continue

                # 独立任务过滤
                if is_independent is not None:
                    is_task_independent = not task.get("story_id")
                    if is_independent != is_task_independent:
                        continue

                filtered_tasks.append(task)

            # 分页处理
            if offset:
                filtered_tasks = filtered_tasks[offset:]
            if limit:
                filtered_tasks = filtered_tasks[:limit]

            return filtered_tasks

        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []

    def delete_task(self, task_id: str) -> bool:
        """删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        try:
            # 先检查任务是否存在
            existing_task = self.get_task(task_id)
            if not existing_task:
                raise ValueError(f"任务 {task_id} 不存在")

            return self._db_service.delete_task(task_id)
        except Exception as e:
            logger.error(f"删除任务 {task_id} 失败: {e}")
            return False
