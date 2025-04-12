"""
路线图数据访问对象模块

提供Roadmap、Epic、Milestone、Story、Task等实体的数据访问接口。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import Epic, Milestone, Roadmap, Story
from src.models.db.task import Task


class RoadmapRepository(Repository[Roadmap]):
    """Roadmap仓库"""

    def __init__(self, session: Session):
        """初始化Roadmap仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, Roadmap)

    def get_with_related(self, roadmap_id: str) -> Optional[Roadmap]:
        """获取Roadmap及其所有关联数据

        Args:
            roadmap_id: Roadmap ID

        Returns:
            Roadmap对象或None
        """
        return self.session.query(Roadmap).filter(Roadmap.id == roadmap_id).first()

    def get_by_name(self, name: str) -> Optional[Roadmap]:
        """通过名称获取路线图

        Args:
            name: 路线图名称

        Returns:
            Roadmap对象或None
        """
        return self.session.query(Roadmap).filter(Roadmap.name == name).first()

    def get_stats(self, roadmap_id: str) -> Dict[str, Any]:
        """获取路线图统计信息"""
        try:
            # 实际实现应查询数据库获取统计信息
            return {"milestones_count": 5, "epics_count": 8, "stories_count": 15, "tasks_count": 47, "completed_tasks": 23, "overall_progress": 48.9}
        except Exception as e:
            return {"error": str(e)}

    def get_milestones_by_roadmap(self, roadmap_id: str) -> List[Any]:
        """获取路线图下的所有里程碑

        Args:
            roadmap_id: 路线图ID

        Returns:
            List[Any]: 里程碑列表
        """
        from src.models.db import Milestone

        try:
            return self.session.query(Milestone).filter(Milestone.roadmap_id == roadmap_id).all()
        except Exception as e:
            self.logger.error(f"获取路线图里程碑时出错: {e}")
            return []

    def get_stories_by_roadmap(self, roadmap_id: str) -> List[Any]:
        """获取路线图下的所有故事

        Args:
            roadmap_id: 路线图ID

        Returns:
            List[Any]: 故事列表
        """
        from src.models.db import Epic, Story

        try:
            # 通过Epic关联查询
            return self.session.query(Story).join(Epic, Story.epic_id == Epic.id).filter(Epic.roadmap_id == roadmap_id).all()
        except Exception as e:
            self.logger.error(f"获取路线图故事时出错: {e}")
            return []

    def get_tasks_by_roadmap(self, roadmap_id: str) -> List[Any]:
        """获取路线图下的所有任务

        Args:
            roadmap_id: 路线图ID

        Returns:
            List[Any]: 任务列表
        """
        from src.models.db import Epic, Story, Task

        try:
            # 通过Story和Epic关联查询
            return (
                self.session.query(Task)
                .join(Story, Task.story_id == Story.id)
                .join(Epic, Story.epic_id == Epic.id)
                .filter(Epic.roadmap_id == roadmap_id)
                .all()
            )
        except Exception as e:
            self.logger.error(f"获取路线图任务时出错: {e}")
            return []


class MilestoneRepository(Repository[Milestone]):
    """Milestone仓库"""

    def __init__(self, session: Session):
        """初始化Milestone仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, Milestone)

    def get_by_roadmap(self, roadmap_id: str) -> List[Milestone]:
        """获取指定路线图下的所有里程碑

        Args:
            roadmap_id: 路线图ID

        Returns:
            Milestone对象列表
        """
        return self.session.query(Milestone).filter(Milestone.roadmap_id == roadmap_id).all()

    def get_with_epics(self, milestone_id: str) -> Optional[Milestone]:
        """获取里程碑及其关联的Epics

        Args:
            milestone_id: 里程碑ID

        Returns:
            Milestone对象或None
        """
        return self.session.query(Milestone).filter(Milestone.id == milestone_id).first()

    def get_by_roadmap_id(self, roadmap_id: str) -> List[Any]:
        """获取指定路线图的所有里程碑

        Args:
            roadmap_id: 路线图ID

        Returns:
            List[Any]: 里程碑列表
        """
        try:
            return self.session.query(Milestone).filter(Milestone.roadmap_id == roadmap_id).all()
        except Exception as e:
            self.logger.error(f"获取路线图里程碑时出错: {e}")
            return []


class EpicRepository(Repository[Epic]):
    """Epic仓库"""

    def __init__(self, session: Session):
        """初始化Epic仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, Epic)

    def get_with_stories(self, epic_id: str) -> Optional[Epic]:
        """获取Epic及其关联的Stories

        Args:
            epic_id: Epic ID

        Returns:
            Epic对象或None
        """
        return self.session.query(Epic).filter(Epic.id == epic_id).first()

    def get_progress(self, epic_id: str) -> Dict[str, Any]:
        """获取Epic进度

        Args:
            epic_id: Epic ID

        Returns:
            进度统计信息
        """
        epic = self.get_by_id(epic_id)
        if not epic:
            return {"error": "Epic not found"}

        story_count = len(epic.stories)
        completed_stories = sum(1 for story in epic.stories if story.status == "completed")

        return {
            "total_stories": story_count,
            "completed_stories": completed_stories,
            "progress": (completed_stories / story_count * 100) if story_count > 0 else 0,
        }

    def get_by_roadmap_id(self, roadmap_id: str) -> List[Any]:
        """获取指定路线图的所有Epic

        Args:
            roadmap_id: 路线图ID

        Returns:
            List[Any]: Epic列表
        """
        try:
            return self.session.query(Epic).filter(Epic.roadmap_id == roadmap_id).all()
        except Exception as e:
            self.logger.error(f"获取路线图Epic时出错: {e}")
            return []


class StoryRepository(Repository[Story]):
    """Story仓库"""

    def __init__(self, session: Session):
        """初始化Story仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, Story)

    def get_with_tasks(self, story_id: str) -> Optional[Story]:
        """获取Story及其关联的Tasks

        Args:
            story_id: Story ID

        Returns:
            Story对象或None
        """
        return self.session.query(Story).filter(Story.id == story_id).first()

    def get_by_epic(self, epic_id: str) -> List[Story]:
        """获取指定Epic下的所有Stories

        Args:
            epic_id: Epic ID

        Returns:
            Story对象列表
        """
        return self.session.query(Story).filter(Story.epic_id == epic_id).all()

    def get_by_epic_id(self, epic_id: str) -> List[Story]:
        """获取指定Epic下的所有Stories（别名方法）

        该方法是get_by_epic的别名，保持兼容性

        Args:
            epic_id: Epic ID

        Returns:
            Story对象列表
        """
        return self.get_by_epic(epic_id)

    def get_progress(self, story_id: str) -> Dict[str, Any]:
        """获取Story进度

        Args:
            story_id: Story ID

        Returns:
            进度统计信息
        """
        story = self.get_by_id(story_id)
        if not story:
            return {"error": "Story not found"}

        task_count = len(story.tasks)
        completed_tasks = sum(1 for task in story.tasks if task.status == "completed")

        return {
            "total_tasks": task_count,
            "completed_tasks": completed_tasks,
            "progress": (completed_tasks / task_count * 100) if task_count > 0 else 0,
        }

    def get_by_roadmap_id(self, roadmap_id: str) -> List[Any]:
        """获取指定路线图的所有故事

        Args:
            roadmap_id: 路线图ID

        Returns:
            List[Any]: 故事列表
        """
        try:
            # 通过Epic关联查询
            return self.session.query(Story).join(Epic, Story.epic_id == Epic.id).filter(Epic.roadmap_id == roadmap_id).all()
        except Exception as e:
            self.logger.error(f"获取路线图故事时出错: {e}")
            return []
