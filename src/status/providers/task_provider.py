# src/status/providers/task_provider.py

import logging
from typing import Any, Dict

from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)


def get_task_status_summary() -> Dict[str, Any]:
    """
    提供 Task 状态摘要。

    Returns:
        包含任务统计信息的字典 (total, by_status)。
    """
    logger.debug("获取 Task 状态摘要...")
    summary = {"total": 0, "by_status": {}}
    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            task_repo = TaskRepository(session)
            # 获取所有任务以进行统计 - 对于大量任务可能需要优化
            all_tasks = task_repo.get_all()
            summary["total"] = len(all_tasks)
            for task in all_tasks:
                summary["by_status"][task.status] = summary["by_status"].get(task.status, 0) + 1
        logger.debug(f"Task 状态摘要: {summary}")
        return summary
    except Exception as e:
        logger.error(f"获取 Task 状态摘要时出错: {e}", exc_info=True)
        return {"error": f"获取 Task 状态摘要失败: {e}"}
