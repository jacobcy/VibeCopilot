"""
任务状态提供者模块

实现任务的状态提供者接口，提供任务状态信息。
"""

import logging
from typing import Any, Dict, List, Optional

from src.status.interfaces import IStatusProvider

logger = logging.getLogger(__name__)


class TaskStatusProvider(IStatusProvider):
    """任务状态提供者"""

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "task"

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """获取任务状态

        Args:
            entity_id: 可选，任务ID。不提供则获取整体任务状态。

        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            # 获取整体任务状态
            if not entity_id:
                # 返回示例数据
                return {
                    "domain": self.domain,
                    "health": 100,
                    "task_count": 3,
                    "pending_tasks": 1,
                    "in_progress_tasks": 1,
                    "completed_tasks": 1,
                    "status_distribution": {"todo": 1, "in_progress": 1, "completed": 1},
                    "suggestions": ["使用 'task create' 创建新任务", "使用 'task update' 更新任务状态"],
                }

            # 获取特定任务状态
            # 这里返回模拟数据，实际实现应该查询数据库
            return {
                "id": entity_id,
                "title": f"Task {entity_id}",
                "status": "in_progress",
                "assignee": "未分配",
                "priority": "P2",
                "health": 100,
            }

        except Exception as e:
            logger.error(f"获取任务状态时出错: {e}")
            return {
                "error": str(e),
                "code": "TASK_STATUS_ERROR",
                "suggestions": ["检查任务数据库连接", "确认任务ID是否存在"],
            }

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
            # 示例实现，实际应更新数据库
            valid_statuses = ["todo", "in_progress", "completed", "canceled"]
            if status not in valid_statuses:
                return {
                    "error": f"无效的任务状态: {status}",
                    "valid_statuses": valid_statuses,
                    "updated": False,
                }

            # 返回模拟更新结果
            return {"id": entity_id, "old_status": "todo", "new_status": status, "updated": True}

        except Exception as e:
            logger.error(f"更新任务状态时出错: {e}")
            return {"error": str(e), "updated": False}

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出任务实体

        Args:
            status: 可选，筛选特定状态的任务

        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        try:
            # 返回示例任务数据
            tasks = [
                {"id": "T001", "title": "完成任务状态提供者", "status": "completed", "priority": "P1"},
                {
                    "id": "T002",
                    "title": "实现Task类SQLAlchemy模型",
                    "status": "in_progress",
                    "priority": "P1",
                },
                {"id": "T003", "title": "添加任务管理UI", "status": "todo", "priority": "P2"},
            ]

            # 如果指定了状态，进行过滤
            if status:
                tasks = [t for t in tasks if t.get("status") == status]

            return tasks

        except Exception as e:
            logger.error(f"列出任务时出错: {e}")
            return []
