"""
数据库服务模块
"""
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Epic, Label, Story, Task
from .repository import EpicRepository, LabelRepository, StoryRepository, TaskRepository

T = TypeVar("T", bound=Base)


class DbService:
    """数据库服务类，提供纯粹的数据库操作"""

    def __init__(self, db_url: str = "sqlite:///tasks.db"):
        """初始化

        Args:
            db_url: 数据库连接URL
        """
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # 仓库实例
        self._epic_repo = None
        self._story_repo = None
        self._task_repo = None
        self._label_repo = None

    def init_db(self):
        """初始化数据库"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    @property
    def epic_repo(self) -> EpicRepository:
        """获取Epic仓库实例"""
        if not self._epic_repo:
            self._epic_repo = EpicRepository(self.get_session())
        return self._epic_repo

    @property
    def story_repo(self) -> StoryRepository:
        """获取Story仓库实例"""
        if not self._story_repo:
            self._story_repo = StoryRepository(self.get_session())
        return self._story_repo

    @property
    def task_repo(self) -> TaskRepository:
        """获取Task仓库实例"""
        if not self._task_repo:
            self._task_repo = TaskRepository(self.get_session())
        return self._task_repo

    @property
    def label_repo(self) -> LabelRepository:
        """获取Label仓库实例"""
        if not self._label_repo:
            self._label_repo = LabelRepository(self.get_session())
        return self._label_repo

    def transaction(self, func, *args, **kwargs):
        """事务处理

        执行函数并处理事务提交和回滚

        Args:
            func: 要执行的函数
            args: 位置参数
            kwargs: 命名参数

        Returns:
            函数执行结果
        """
        session = self.get_session()
        try:
            result = func(*args, **kwargs, session=session)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # Epic操作
    def create_epic(self, data: Dict[str, Any]) -> Epic:
        """创建Epic

        Args:
            data: Epic数据

        Returns:
            创建的Epic实体
        """
        return self.epic_repo.create(Epic, data)

    def get_epic(self, epic_id: str) -> Optional[Epic]:
        """获取Epic

        Args:
            epic_id: Epic ID

        Returns:
            Epic实体或None
        """
        return self.epic_repo.get_by_id(Epic, epic_id)

    def get_all_epics(self) -> List[Epic]:
        """获取所有Epic

        Returns:
            Epic实体列表
        """
        return self.epic_repo.get_all(Epic)

    def update_epic(self, epic_id: str, data: Dict[str, Any]) -> Optional[Epic]:
        """更新Epic

        Args:
            epic_id: Epic ID
            data: 更新数据

        Returns:
            更新后的Epic实体或None
        """
        return self.epic_repo.update(Epic, epic_id, data)

    def delete_epic(self, epic_id: str) -> bool:
        """删除Epic

        Args:
            epic_id: Epic ID

        Returns:
            是否删除成功
        """
        return self.epic_repo.delete(Epic, epic_id)

    def get_epic_progress(self, epic_id: str) -> Dict[str, Any]:
        """获取Epic进度

        Args:
            epic_id: Epic ID

        Returns:
            进度统计信息
        """
        return self.epic_repo.get_progress(epic_id)

    # Story操作
    def create_story(self, data: Dict[str, Any]) -> Story:
        """创建Story

        Args:
            data: Story数据

        Returns:
            创建的Story实体
        """
        return self.story_repo.create(Story, data)

    def get_story(self, story_id: str) -> Optional[Story]:
        """获取Story

        Args:
            story_id: Story ID

        Returns:
            Story实体或None
        """
        return self.story_repo.get_by_id(Story, story_id)

    def get_all_stories(self) -> List[Story]:
        """获取所有Story

        Returns:
            Story实体列表
        """
        return self.story_repo.get_all(Story)

    def get_stories_by_epic(self, epic_id: str) -> List[Story]:
        """获取指定Epic下的所有Stories

        Args:
            epic_id: Epic ID

        Returns:
            Story实体列表
        """
        return self.story_repo.get_by_epic(epic_id)

    def update_story(self, story_id: str, data: Dict[str, Any]) -> Optional[Story]:
        """更新Story

        Args:
            story_id: Story ID
            data: 更新数据

        Returns:
            更新后的Story实体或None
        """
        return self.story_repo.update(Story, story_id, data)

    def delete_story(self, story_id: str) -> bool:
        """删除Story

        Args:
            story_id: Story ID

        Returns:
            是否删除成功
        """
        return self.story_repo.delete(Story, story_id)

    def get_story_progress(self, story_id: str) -> Dict[str, Any]:
        """获取Story进度

        Args:
            story_id: Story ID

        Returns:
            进度统计信息
        """
        return self.story_repo.get_progress(story_id)

    # Task操作
    def create_task(self, data: Dict[str, Any]) -> Task:
        """创建Task

        Args:
            data: Task数据

        Returns:
            创建的Task实体
        """
        return self.task_repo.create(Task, data)

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取Task

        Args:
            task_id: Task ID

        Returns:
            Task实体或None
        """
        return self.task_repo.get_by_id(Task, task_id)

    def get_all_tasks(self) -> List[Task]:
        """获取所有Task

        Returns:
            Task实体列表
        """
        return self.task_repo.get_all(Task)

    def get_tasks_by_story(self, story_id: str) -> List[Task]:
        """获取指定Story下的所有Tasks

        Args:
            story_id: Story ID

        Returns:
            Task实体列表
        """
        return self.task_repo.get_by_story(story_id)

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Optional[Task]:
        """更新Task

        Args:
            task_id: Task ID
            data: 更新数据

        Returns:
            更新后的Task实体或None
        """
        return self.task_repo.update(Task, task_id, data)

    def delete_task(self, task_id: str) -> bool:
        """删除Task

        Args:
            task_id: Task ID

        Returns:
            是否删除成功
        """
        return self.task_repo.delete(Task, task_id)

    def add_task_label(self, task_id: str, label_id: str) -> bool:
        """为任务添加标签

        Args:
            task_id: 任务ID
            label_id: 标签ID

        Returns:
            是否添加成功
        """
        return self.task_repo.add_label(task_id, label_id)

    def remove_task_label(self, task_id: str, label_id: str) -> bool:
        """移除任务标签

        Args:
            task_id: 任务ID
            label_id: 标签ID

        Returns:
            是否移除成功
        """
        return self.task_repo.remove_label(task_id, label_id)

    # Label操作
    def create_label(self, data: Dict[str, Any]) -> Label:
        """创建Label

        Args:
            data: Label数据

        Returns:
            创建的Label实体
        """
        return self.label_repo.create(Label, data)

    def get_label(self, label_id: str) -> Optional[Label]:
        """获取Label

        Args:
            label_id: Label ID

        Returns:
            Label实体或None
        """
        return self.label_repo.get_by_id(Label, label_id)

    def get_label_by_name(self, name: str) -> Optional[Label]:
        """根据名称获取标签

        Args:
            name: 标签名称

        Returns:
            标签对象或None
        """
        return self.label_repo.get_by_name(name)

    def get_all_labels(self) -> List[Label]:
        """获取所有Label

        Returns:
            Label实体列表
        """
        return self.label_repo.get_all(Label)

    def update_label(self, label_id: str, data: Dict[str, Any]) -> Optional[Label]:
        """更新Label

        Args:
            label_id: Label ID
            data: 更新数据

        Returns:
            更新后的Label实体或None
        """
        return self.label_repo.update(Label, label_id, data)

    def delete_label(self, label_id: str) -> bool:
        """删除Label

        Args:
            label_id: Label ID

        Returns:
            是否删除成功
        """
        return self.label_repo.delete(Label, label_id)

    def get_tasks_by_label(self, label_id: str) -> List[Task]:
        """获取具有指定标签的所有任务

        Args:
            label_id: 标签ID

        Returns:
            任务对象列表
        """
        return self.label_repo.get_tasks_by_label(label_id)
