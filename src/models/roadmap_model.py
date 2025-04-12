"""
路线图模型模块

提供路线图相关的数据模型和转换功能。
"""

from datetime import datetime
from typing import Dict, List, Optional

from src.models.db.epic import Epic
from src.models.db.roadmap import Roadmap
from src.models.db.story import Story
from src.models.db.task import Task


class RoadmapModel:
    """路线图模型，用于管理和转换路线图数据"""

    @staticmethod
    def create_roadmap(data: Dict) -> Roadmap:
        """从字典数据创建路线图实例

        Args:
            data: 路线图数据字典

        Returns:
            Roadmap: 路线图实例
        """
        roadmap_data = {
            "title": data.get("title"),
            "description": data.get("description"),
            "version": data.get("version", "1.0.0"),
            "status": data.get("status", "active"),
            "tags": data.get("tags"),
        }
        return Roadmap(**roadmap_data)

    @staticmethod
    def create_epic(data: Dict) -> Epic:
        """从字典数据创建Epic实例

        Args:
            data: Epic数据字典

        Returns:
            Epic: Epic实例
        """
        epic_data = {
            "title": data.get("title"),
            "description": data.get("description"),
            "status": data.get("status", "draft"),
            "priority": data.get("priority", "medium"),
            "roadmap_id": data.get("roadmap_id"),
        }
        return Epic(**epic_data)

    @staticmethod
    def create_story(data: Dict) -> Story:
        """从字典数据创建Story实例

        Args:
            data: Story数据字典

        Returns:
            Story: Story实例
        """
        story_data = {
            "title": data.get("title"),
            "description": data.get("description"),
            "acceptance_criteria": data.get("acceptance_criteria"),
            "status": data.get("status", "backlog"),
            "priority": data.get("priority", "medium"),
            "points": data.get("points", 0),
            "epic_id": data.get("epic_id"),
        }
        return Story(**story_data)

    @staticmethod
    def create_task(data: Dict) -> Task:
        """从字典数据创建Task实例

        Args:
            data: Task数据字典

        Returns:
            Task: Task实例
        """
        task_data = {
            "title": data.get("title"),
            "description": data.get("description"),
            "status": data.get("status", "todo"),
            "priority": data.get("priority", "medium"),
            "estimated_hours": data.get("estimated_hours", 0),
            "is_completed": data.get("is_completed", False),
            "story_id": data.get("story_id"),
            "assignee": data.get("assignee"),
            "labels": data.get("labels", []),
        }
        return Task(**task_data)

    @staticmethod
    def to_dict(model: object) -> Dict:
        """将模型实例转换为字典

        Args:
            model: 模型实例 (Roadmap, Epic, Story, Task)

        Returns:
            Dict: 模型数据字典
        """
        if hasattr(model, "to_dict"):
            return model.to_dict()
        return {}

    @staticmethod
    def validate_status(model_type: str, status: str) -> bool:
        """验证状态值是否有效

        Args:
            model_type: 模型类型 ("roadmap", "epic", "story", "task")
            status: 状态值

        Returns:
            bool: 状态是否有效
        """
        valid_statuses = {
            "roadmap": ["active", "archived", "draft"],
            "epic": ["draft", "in_progress", "completed", "archived"],
            "story": ["backlog", "ready", "in_progress", "review", "completed"],
            "task": ["todo", "in_progress", "review", "done"],
        }
        return status in valid_statuses.get(model_type, [])

    @staticmethod
    def validate_priority(priority: str) -> bool:
        """验证优先级值是否有效

        Args:
            priority: 优先级值

        Returns:
            bool: 优先级是否有效
        """
        valid_priorities = ["low", "medium", "high", "critical"]
        return priority in valid_priorities

    @staticmethod
    def get_default_status(model_type: str) -> str:
        """获取模型类型的默认状态

        Args:
            model_type: 模型类型 ("roadmap", "epic", "story", "task")

        Returns:
            str: 默认状态值
        """
        defaults = {
            "roadmap": "active",
            "epic": "draft",
            "story": "backlog",
            "task": "todo",
        }
        return defaults.get(model_type, "")
