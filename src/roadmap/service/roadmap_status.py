"""
路线图状态服务模块

提供路线图状态的检查和管理功能。
"""

import logging
from typing import Any, Dict, List, Optional, Union

from src.db.repositories.roadmap_repository import RoadmapRepository, StoryRepository
from src.db.repositories.task_repository import TaskRepository
from src.models.db.epic import Epic
from src.models.db.milestone import Milestone
from src.models.db.roadmap import Roadmap
from src.models.db.story import Story
from src.models.db.task import Task
from src.roadmap.service.roadmap_service import RoadmapService

logger = logging.getLogger(__name__)


class RoadmapStatus:
    """路线图状态服务"""

    def __init__(self, roadmap_service: RoadmapService):
        """初始化路线图状态服务

        Args:
            roadmap_service: 路线图服务实例
        """
        self._service = roadmap_service
        self._roadmap_repo = RoadmapRepository(self._service.session)
        self._story_repo = StoryRepository(self._service.session)
        self._task_repo = TaskRepository(self._service.session)

    def check_roadmap_status(self, check_type: str = "roadmap", element_id: Optional[str] = None) -> Dict[str, Any]:
        """检查路线图状态

        Args:
            check_type: 检查类型 ("roadmap", "epic", "story", "task")
            element_id: 元素ID (可选)

        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            if check_type == "roadmap":
                if element_id:
                    roadmap = self._roadmap_repo.get_with_related(element_id)
                    if not roadmap:
                        return {"success": False, "error": f"未找到路线图: {element_id}", "code": "ROADMAP_NOT_FOUND"}
                else:
                    # 获取活动路线图
                    roadmap = self._service.get_active_roadmap()
                    if not roadmap:
                        return {"success": False, "error": "未找到活动路线图", "code": "NO_ACTIVE_ROADMAP"}

                return self._check_overall_status(roadmap)
            else:
                if not element_id:
                    return {"success": False, "error": f"检查{check_type}状态时需要提供element_id", "code": "MISSING_ELEMENT_ID"}

                return self._check_element_status(check_type, element_id)

        except Exception as e:
            logger.error(f"检查路线图状态时出错: {e}")
            return {"success": False, "error": str(e), "code": "STATUS_CHECK_ERROR"}

    def _check_overall_status(self, roadmap: Roadmap) -> Dict[str, Any]:
        """检查整体路线图状态

        Args:
            roadmap: 路线图实例

        Returns:
            Dict[str, Any]: 状态信息
        """
        stats = self._roadmap_repo.get_stats(roadmap.id)

        return {
            "success": True,
            "status": {
                "id": roadmap.id,
                "name": roadmap.title,
                "description": roadmap.description,
                "version": roadmap.version,
                "status": roadmap.status,
                "tags": roadmap.tags,
                "created_at": roadmap.created_at,
                "updated_at": roadmap.updated_at,
                "stats": stats,
                "epics": [
                    {
                        "id": epic.id,
                        "title": epic.title,
                        "status": epic.status,
                        "priority": epic.priority,
                        "progress": self._calculate_epic_progress(epic),
                    }
                    for epic in roadmap.epics
                ],
                "milestones": [
                    {
                        "id": milestone.id,
                        "title": milestone.title,
                        "status": milestone.status,
                        "progress": self._calculate_milestone_progress(milestone),
                    }
                    for milestone in roadmap.milestones
                ],
                "health": self._calculate_roadmap_health(stats),
            },
        }

    def _check_element_status(self, element_type: str, element_id: str) -> Dict[str, Any]:
        """检查特定元素状态

        Args:
            element_type: 元素类型
            element_id: 元素ID

        Returns:
            Dict[str, Any]: 状态信息
        """
        if element_type == "epic":
            epic = self._roadmap_repo.get_with_stories(element_id)
            if not epic:
                return {"success": False, "error": f"未找到Epic: {element_id}", "code": "EPIC_NOT_FOUND"}

            progress = self._calculate_epic_progress(epic)
            return {
                "success": True,
                "status": {
                    "id": epic.id,
                    "title": epic.title,
                    "description": epic.description,
                    "status": epic.status,
                    "priority": epic.priority,
                    "created_at": epic.created_at,
                    "updated_at": epic.updated_at,
                    "progress": progress,
                    "stories": [
                        {"id": story.id, "title": story.title, "status": story.status, "progress": self._calculate_story_progress(story)}
                        for story in epic.stories
                    ],
                    "health": self._calculate_health_from_progress(progress),
                },
            }

        elif element_type == "story":
            story = self._story_repo.get_with_tasks(element_id)
            if not story:
                return {"success": False, "error": f"未找到Story: {element_id}", "code": "STORY_NOT_FOUND"}

            progress = self._calculate_story_progress(story)
            return {
                "success": True,
                "status": {
                    "id": story.id,
                    "title": story.title,
                    "description": story.description,
                    "status": story.status,
                    "priority": story.priority,
                    "points": story.points,
                    "created_at": story.created_at,
                    "updated_at": story.updated_at,
                    "progress": progress,
                    "tasks": [{"id": task.id, "title": task.title, "status": task.status, "assignee": task.assignee} for task in story.tasks],
                    "health": self._calculate_health_from_progress(progress),
                },
            }

        elif element_type == "task":
            task = self._task_repo.get_by_id_with_comments(element_id)
            if not task:
                return {"success": False, "error": f"未找到Task: {element_id}", "code": "TASK_NOT_FOUND"}

            return {
                "success": True,
                "status": {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "estimated_hours": task.estimated_hours,
                    "is_completed": task.is_completed,
                    "assignee": task.assignee,
                    "labels": task.labels,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "completed_at": task.completed_at,
                    "comments": [
                        {"id": comment.id, "content": comment.content, "author": comment.author, "created_at": comment.created_at}
                        for comment in task.comments
                    ],
                    "health": "good" if task.is_completed else "needs_attention",
                },
            }

        return {"success": False, "error": f"未知元素类型: {element_type}", "code": "UNKNOWN_ELEMENT_TYPE"}

    def _calculate_epic_progress(self, epic: Epic) -> float:
        """计算Epic的进度

        Args:
            epic: Epic实例

        Returns:
            float: 进度百分比
        """
        if not epic.stories:
            return 0.0

        completed = sum(1 for story in epic.stories if story.status == "completed")
        return (completed / len(epic.stories)) * 100

    def _calculate_story_progress(self, story: Story) -> float:
        """计算Story的进度

        Args:
            story: Story实例

        Returns:
            float: 进度百分比
        """
        if not story.tasks:
            return 0.0

        completed = sum(1 for task in story.tasks if task.is_completed)
        return (completed / len(story.tasks)) * 100

    def _calculate_milestone_progress(self, milestone: Milestone) -> float:
        """计算Milestone的进度

        Args:
            milestone: Milestone实例

        Returns:
            float: 进度百分比
        """
        if not milestone.stories:
            return 0.0

        completed = sum(1 for story in milestone.stories if story.status == "completed")
        return (completed / len(milestone.stories)) * 100

    def _calculate_health_from_progress(self, progress: float) -> str:
        """根据进度计算健康状态

        Args:
            progress: 进度百分比

        Returns:
            str: 健康状态
        """
        if progress >= 80:
            return "good"
        elif progress >= 50:
            return "fair"
        else:
            return "needs_attention"

    def _calculate_roadmap_health(self, stats: Dict[str, Any]) -> str:
        """计算路线图整体健康状态

        Args:
            stats: 统计信息

        Returns:
            str: 健康状态
        """
        if "error" in stats:
            return "error"

        # 计算整体进度
        overall_progress = stats.get("overall_progress", 0)
        return self._calculate_health_from_progress(overall_progress)
