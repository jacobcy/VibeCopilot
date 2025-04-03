"""
数据库访问对象模块
"""
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .models import Base, Epic, Label, Story, Task

T = TypeVar("T", bound=Base)


class DatabaseRepository:
    """数据库访问对象基类"""

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        self.session = session

    def create(self, model_class: Type[T], data: Dict[str, Any]) -> T:
        """创建记录

        Args:
            model_class: 模型类
            data: 数据字典

        Returns:
            新创建的实体对象
        """
        try:
            instance = model_class.from_dict(data)
            self.session.add(instance)
            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def get_by_id(self, model_class: Type[T], id: str) -> Optional[T]:
        """根据ID获取记录

        Args:
            model_class: 模型类
            id: 实体ID

        Returns:
            实体对象或None
        """
        return self.session.query(model_class).filter(model_class.id == id).first()

    def get_all(self, model_class: Type[T]) -> List[T]:
        """获取所有记录

        Args:
            model_class: 模型类

        Returns:
            实体对象列表
        """
        return self.session.query(model_class).all()

    def update(self, model_class: Type[T], id: str, data: Dict[str, Any]) -> Optional[T]:
        """更新记录

        Args:
            model_class: 模型类
            id: 实体ID
            data: 更新数据

        Returns:
            更新后的实体对象或None
        """
        try:
            instance = self.get_by_id(model_class, id)
            if not instance:
                return None

            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def delete(self, model_class: Type[T], id: str) -> bool:
        """删除记录

        Args:
            model_class: 模型类
            id: 实体ID

        Returns:
            是否删除成功
        """
        try:
            instance = self.get_by_id(model_class, id)
            if not instance:
                return False

            self.session.delete(instance)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e

    def query_by_filter(self, model_class: Type[T], filters: Dict[str, Any]) -> List[T]:
        """根据过滤条件查询

        Args:
            model_class: 模型类
            filters: 过滤条件

        Returns:
            符合条件的实体对象列表
        """
        query = self.session.query(model_class)

        for attr, value in filters.items():
            if hasattr(model_class, attr):
                query = query.filter(getattr(model_class, attr) == value)

        return query.all()


class EpicRepository(DatabaseRepository):
    """Epic仓库"""

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
        epic = self.get_by_id(Epic, epic_id)
        if not epic:
            return {"error": "Epic not found"}

        story_count = len(epic.stories)
        completed_stories = sum(1 for story in epic.stories if story.status == "completed")

        return {
            "total_stories": story_count,
            "completed_stories": completed_stories,
            "progress": (completed_stories / story_count * 100) if story_count > 0 else 0,
        }


class StoryRepository(DatabaseRepository):
    """Story仓库"""

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
        story = self.get_by_id(Story, story_id)
        if not story:
            return {"error": "Story not found"}

        task_count = len(story.tasks)
        completed_tasks = sum(1 for task in story.tasks if task.status == "completed")

        return {
            "total_tasks": task_count,
            "completed_tasks": completed_tasks,
            "progress": (completed_tasks / task_count * 100) if task_count > 0 else 0,
        }


class TaskRepository(DatabaseRepository):
    """Task仓库"""

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
            task = self.get_by_id(Task, task_id)
            label = self.session.query(Label).filter(Label.id == label_id).first()

            if not task or not label:
                return False

            if label not in task.labels:
                task.labels.append(label)
                self.session.commit()

            return True
        except SQLAlchemyError as e:
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
            task = self.get_by_id(Task, task_id)
            label = self.session.query(Label).filter(Label.id == label_id).first()

            if not task or not label:
                return False

            if label in task.labels:
                task.labels.remove(label)
                self.session.commit()

            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise e


class LabelRepository(DatabaseRepository):
    """标签仓库"""

    def get_by_name(self, name: str) -> Optional[Label]:
        """根据名称获取标签

        Args:
            name: 标签名称

        Returns:
            标签对象或None
        """
        return self.session.query(Label).filter(Label.name == name).first()

    def get_tasks_by_label(self, label_id: str) -> List[Task]:
        """获取具有指定标签的所有任务

        Args:
            label_id: 标签ID

        Returns:
            任务对象列表
        """
        label = self.get_by_id(Label, label_id)
        return label.tasks if label else []
