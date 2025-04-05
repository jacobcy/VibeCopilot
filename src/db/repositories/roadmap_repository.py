"""
路线图数据访问对象模块

提供Epic、Story、Task和Label等实体的数据访问接口。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repository import Repository
from src.models.db import Epic, Label, Story, Task


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


class TaskRepository(Repository[Task]):
    """Task仓库"""

    def __init__(self, session: Session):
        """初始化Task仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, Task)

    def get_by_story(self, story_id: str) -> List[Task]:
        """获取指定Story下的所有Tasks

        Args:
            story_id: Story ID

        Returns:
            Task对象列表
        """
        return self.session.query(Task).filter(Task.story_id == story_id).all()

    def add_label(self, task_id: str, label_id: str) -> bool:
        """为任务添加标签

        Args:
            task_id: 任务ID
            label_id: 标签ID

        Returns:
            是否添加成功
        """
        try:
            task = self.get_by_id(task_id)
            label = self.session.query(Label).filter(Label.id == label_id).first()

            if not task or not label:
                return False

            if label not in task.labels:
                task.labels.append(label)
                self.session.commit()
                return True

            return False
        except Exception as e:
            self.session.rollback()
            raise e

    def remove_label(self, task_id: str, label_id: str) -> bool:
        """移除任务标签

        Args:
            task_id: 任务ID
            label_id: 标签ID

        Returns:
            是否移除成功
        """
        try:
            task = self.get_by_id(task_id)
            label = self.session.query(Label).filter(Label.id == label_id).first()

            if not task or not label:
                return False

            if label in task.labels:
                task.labels.remove(label)
                self.session.commit()
                return True

            return False
        except Exception as e:
            self.session.rollback()
            raise e


class LabelRepository(Repository[Label]):
    """Label仓库"""

    def __init__(self, session: Session):
        """初始化Label仓库

        Args:
            session: SQLAlchemy会话对象
        """
        super().__init__(session, Label)

    def get_by_name(self, name: str) -> Optional[Label]:
        """通过名称获取标签

        Args:
            name: 标签名称

        Returns:
            Label对象或None
        """
        return self.session.query(Label).filter(Label.name == name).first()

    def get_tasks(self, label_id: str) -> List[Task]:
        """获取使用指定标签的所有任务

        Args:
            label_id: 标签ID

        Returns:
            Task对象列表
        """
        label = self.get_by_id(label_id)
        if not label:
            return []

        return label.tasks
