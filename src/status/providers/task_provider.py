# src/status/providers/task_provider.py

import logging
from typing import Any, Dict, List, Optional

from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository
from src.status.interfaces import IStatusProvider

logger = logging.getLogger(__name__)


class TaskStatusProvider(IStatusProvider):
    """任务状态提供者"""

    def __init__(self):
        """初始化任务状态提供者"""
        self._db_session = None

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "task"

    def _get_db_session(self):
        if self._db_session is None:
            session_factory = get_session_factory()
            self._db_session = session_factory()
        return self._db_session

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取任务状态

        Args:
            entity_id: 可选，任务ID。不提供则获取任务系统整体状态。

        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            session = self._get_db_session()
            try:
                task_repo = TaskRepository(session)

                # 获取整体状态
                if not entity_id:
                    all_tasks = task_repo.get_all()
                    by_status = {}
                    for task in all_tasks:
                        by_status[task.status] = by_status.get(task.status, 0) + 1

                    return {"domain": self.domain, "total": len(all_tasks), "by_status": by_status}

                # 获取特定任务状态
                task = task_repo.get_by_id(entity_id)
                if not task:
                    return {"error": f"任务不存在: {entity_id}"}

                return {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "domain": self.domain,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"获取任务状态时出错: {e}")
            return {"error": str(e)}

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新任务状态

        Args:
            entity_id: 任务ID
            status: 新状态
            **kwargs: 附加参数

        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            session = self._get_db_session()
            try:
                task_repo = TaskRepository(session)
                result = task_repo.update_status(entity_id, status)

                if result:
                    return {"updated": True, "entity_id": entity_id, "status": status}
                else:
                    return {"updated": False, "error": "更新失败，任务可能不存在"}
            finally:
                session.close()
        except Exception as e:
            logger.error(f"更新任务状态时出错: {e}")
            return {"error": str(e), "updated": False}

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出任务

        Args:
            status: 可选，筛选特定状态的任务

        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        try:
            session = self._get_db_session()
            try:
                task_repo = TaskRepository(session)
                tasks = task_repo.get_all(status=status)

                return [
                    {
                        "id": task.id,
                        "title": task.title,
                        "status": task.status,
                        "type": "task",
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                    }
                    for task in tasks
                ]
            finally:
                session.close()
        except Exception as e:
            logger.error(f"列出任务时出错: {e}")
            return []


# 保持向后兼容的函数
def get_task_status_summary() -> Dict[str, Any]:
    """
    提供 Task 状态摘要。

    Returns:
        包含任务统计信息的字典 (total, by_status)。
    """
    provider = TaskStatusProvider()
    return provider.get_status()
