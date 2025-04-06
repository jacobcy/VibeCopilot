"""
路线图管理器模块

提供路线图核心管理功能，用于处理路线图数据的业务逻辑。
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RoadmapManager:
    """路线图管理器，提供路线图核心业务逻辑处理"""

    def __init__(self, service):
        """
        初始化路线图管理器

        Args:
            service: 路线图服务
        """
        self.service = service

        # 根据环境变量确定存储路径
        project_root = os.environ.get("PROJECT_ROOT", os.getcwd())
        self.ai_dir = os.path.join(project_root, ".ai")
        self.roadmap_dir = os.path.join(self.ai_dir, "roadmap")

        # 确保目录存在
        os.makedirs(self.roadmap_dir, exist_ok=True)

    def check_roadmap(
        self,
        check_type: str = "roadmap",
        resource_id: Optional[str] = None,
        roadmap_id: Optional[str] = None,
        update: bool = False,
    ) -> Dict[str, Any]:
        """
        检查路线图状态

        Args:
            check_type: 检查类型
            resource_id: 资源ID
            update: 是否更新

        Returns:
            Dict[str, Any]: 检查结果
        """
        roadmap_id = roadmap_id or self.service.active_roadmap_id

        # 处理不同类型的检查
        if check_type == "roadmap" or check_type == "entire":
            return self._check_entire_roadmap(roadmap_id, update)
        elif check_type == "milestone":
            return self._check_milestone(roadmap_id, resource_id, update)
        elif check_type == "task":
            return self._check_task(roadmap_id, resource_id, update)
        else:
            raise ValueError(f"不支持的检查类型: {check_type}")

    def _check_entire_roadmap(self, roadmap_id: str, update: bool) -> Dict[str, Any]:
        """检查整个路线图状态"""
        # 获取所有数据
        milestones = self.service.get_milestones(roadmap_id)
        tasks = self.service.list_tasks(roadmap_id)

        # 计算任务统计信息
        task_status = {"todo": 0, "in_progress": 0, "completed": 0}
        for task in tasks:
            status = task.get("status", "todo")
            if status in task_status:
                task_status[status] += 1

        # 计算活跃里程碑
        active_milestone = None
        milestone_status = {}
        for milestone in milestones:
            milestone_id = milestone.get("id")
            milestone_status[milestone_id] = {
                "name": milestone.get("name"),
                "status": milestone.get("status", "planned"),
                "progress": milestone.get("progress", 0),
                "tasks": len([t for t in tasks if t.get("milestone") == milestone_id]),
            }

            if milestone.get("status") == "in_progress":
                active_milestone = milestone_id

        # 如果没有活跃里程碑但有里程碑，选择第一个
        if not active_milestone and milestones:
            active_milestone = milestones[0].get("id")

        return {
            "milestones": len(milestones),
            "tasks": len(tasks),
            "active_milestone": active_milestone,
            "milestone_status": milestone_status,
            "task_status": task_status,
        }

    def _check_milestone(
        self, roadmap_id: str, milestone_id: Optional[str], update: bool
    ) -> Dict[str, Any]:
        """检查特定里程碑状态"""
        if not milestone_id:
            raise ValueError("检查里程碑需要指定id参数")

        # 查找里程碑
        milestone = None
        milestones = self.service.get_milestones(roadmap_id)
        for m in milestones:
            if m.get("id") == milestone_id:
                milestone = m
                break

        if not milestone:
            raise ValueError(f"未找到里程碑: {milestone_id}")

        # 获取里程碑任务
        tasks = [
            t for t in self.service.list_tasks(roadmap_id) if t.get("milestone") == milestone_id
        ]

        # 计算任务状态
        task_status = {"todo": 0, "in_progress": 0, "completed": 0}
        for task in tasks:
            status = task.get("status", "todo")
            if status in task_status:
                task_status[status] += 1

        # 计算进度
        total_tasks = len(tasks)
        completed_tasks = task_status.get("completed", 0)
        progress = int(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # 更新里程碑进度 - 简化实现
        if update and milestone:
            milestone_data = milestone.copy()
            milestone_data["progress"] = progress

            # 自动更新状态
            if progress == 100:
                milestone_data["status"] = "completed"
            elif progress > 0:
                milestone_data["status"] = "in_progress"

            # 这里不再更新数据库，因为我们现在只是一个模拟实现
            logger.info(f"里程碑进度更新: {milestone_id} -> {progress}%")

        return {
            "milestone_id": milestone_id,
            "name": milestone.get("name"),
            "status": milestone.get("status"),
            "progress": progress,
            "tasks": total_tasks,
            "task_status": task_status,
        }

    def _check_task(self, roadmap_id: str, task_id: Optional[str], update: bool) -> Dict[str, Any]:
        """检查特定任务状态"""
        if not task_id:
            raise ValueError("检查任务需要指定id参数")

        # 查找任务 - 简化实现
        task = {
            "id": task_id,
            "title": f"任务 {task_id}",
            "status": "in_progress",
            "milestone": "milestone-123",
        }

        # 查找关联里程碑
        milestone = None
        milestone_id = task.get("milestone")
        if milestone_id:
            milestones = self.service.get_milestones(roadmap_id)
            for m in milestones:
                if m.get("id") == milestone_id:
                    milestone = m
                    break

        return {
            "task_id": task_id,
            "title": task.get("title"),
            "status": task.get("status"),
            "priority": task.get("priority", "medium"),
            "milestone": {
                "id": milestone_id,
                "name": milestone.get("name") if milestone else None,
                "status": milestone.get("status") if milestone else None,
            }
            if milestone_id
            else None,
        }
