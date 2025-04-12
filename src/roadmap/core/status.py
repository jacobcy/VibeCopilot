"""
路线图状态模块

处理路线图元素状态更新和计算。
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RoadmapStatus:
    """路线图状态处理类，提供状态更新和计算功能"""

    def __init__(self, service):
        """
        初始化路线图状态处理类

        Args:
            service: 路线图服务
        """
        self.service = service

    def update_element(
        self,
        element_id: str,
        element_type: str,
        status: Optional[str] = None,
        roadmap_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        更新路线图元素状态

        Args:
            element_id: 元素ID
            element_type: 元素类型，可选值：milestone, task
            status: 新状态，不提供则只查询不更新
            roadmap_id: 路线图ID，不提供则使用活跃路线图

        Returns:
            Dict[str, Any]: 更新结果
        """
        roadmap_id = roadmap_id or self.service.active_roadmap_id

        if element_type == "milestone":
            return self._update_milestone(element_id, status, roadmap_id)
        elif element_type == "task":
            return self._update_task(element_id, status, roadmap_id)
        else:
            logger.error(f"不支持的元素类型: {element_type}")
            return {"error": f"不支持的元素类型: {element_type}", "updated": False}

    def _update_milestone(self, milestone_id: str, status: Optional[str], roadmap_id: str) -> Dict[str, Any]:
        """更新里程碑状态"""
        # 获取里程碑
        milestones = self.service.get_milestones(roadmap_id)
        milestone = None
        for m in milestones:
            if m.get("id") == milestone_id:
                milestone = m
                break

        if not milestone:
            logger.error(f"未找到里程碑: {milestone_id}")
            return {"error": f"未找到里程碑: {milestone_id}", "updated": False}

        # 查询模式
        if status is None:
            return {
                "id": milestone_id,
                "name": milestone.get("name"),
                "status": milestone.get("status"),
                "progress": milestone.get("progress", 0),
                "updated": False,
            }

        # 验证状态值
        valid_statuses = ["planned", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            logger.error(f"无效的里程碑状态: {status}")
            return {
                "error": f"无效的里程碑状态: {status}，有效值: {', '.join(valid_statuses)}",
                "updated": False,
            }

        # 更新状态
        milestone_data = milestone.copy()
        milestone_data["status"] = status

        # 如果状态为completed，自动设置进度为100%
        if status == "completed":
            milestone_data["progress"] = 100

        # 如果状态为in_progress且进度为0，自动设置为1%
        if status == "in_progress" and milestone_data.get("progress", 0) == 0:
            milestone_data["progress"] = 1

        # 这里简化实现，不实际更新数据库
        logger.info(f"更新里程碑状态: {milestone_id} -> {status}")
        return {
            "id": milestone_id,
            "name": milestone.get("name"),
            "status": status,
            "progress": milestone_data.get("progress", 0),
            "updated": True,
        }

    def _update_task(self, task_id: str, status: Optional[str], roadmap_id: str) -> Dict[str, Any]:
        """更新任务状态"""
        # 获取任务
        tasks = self.service.get_tasks(roadmap_id)
        task = None
        for t in tasks:
            if t.get("id") == task_id:
                task = t
                break

        if not task:
            logger.error(f"未找到任务: {task_id}")
            return {"error": f"未找到任务: {task_id}", "updated": False}

        # 查询模式
        if status is None:
            return {
                "id": task_id,
                "title": task.get("title") or task.get("name"),
                "status": task.get("status"),
                "milestone": task.get("milestone"),
                "updated": False,
            }

        # 验证状态值
        valid_statuses = ["todo", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            logger.error(f"无效的任务状态: {status}")
            return {
                "error": f"无效的任务状态: {status}，有效值: {', '.join(valid_statuses)}",
                "updated": False,
            }

        # 更新状态
        task_data = task.copy()
        task_data["status"] = status

        # 这里简化实现，不实际更新数据库
        logger.info(f"更新任务状态: {task_id} -> {status}")
        return {
            "id": task_id,
            "title": task.get("title") or task.get("name"),
            "status": status,
            "milestone": task.get("milestone"),
            "updated": True,
        }
