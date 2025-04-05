"""
统一数据库服务模块

为应用程序提供统一的数据库服务接口，管理会话和事务。
"""

import os
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from src.models.db import Base

from . import get_engine, get_session_factory, init_db
from .repositories import (
    EpicRepository,
    LabelRepository,
    StoryRepository,
    TaskRepository,
    TemplateRepository,
    TemplateVariableRepository,
)

# 定义泛型类型
T = TypeVar("T")


class DatabaseService:
    """统一数据库服务类"""

    _instance = None

    def __new__(cls, db_path: Optional[str] = None):
        """单例模式实现

        Args:
            db_path: 数据库文件路径，如果不指定则使用默认路径

        Returns:
            DatabaseService实例
        """
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        """初始化数据库服务

        Args:
            db_path: 数据库文件路径，如果不指定则使用默认路径
        """
        # 防止重复初始化
        if getattr(self, "_initialized", False):
            return

        # 初始化数据库引擎和会话工厂
        self.engine = get_engine(db_path)
        self.session_factory = get_session_factory(self.engine)

        # 初始化数据库
        init_db(self.engine)

        # 初始化仓库
        self._initialize_repositories()

        self._initialized = True

    def _initialize_repositories(self):
        """初始化所有仓库实例"""
        # 使用上下文管理器创建会话
        with self.session_factory() as session:
            # 路线图相关仓库
            self.epic_repo = EpicRepository(session)
            self.story_repo = StoryRepository(session)
            self.task_repo = TaskRepository(session)
            self.label_repo = LabelRepository(session)

            # 模板相关仓库
            self.template_repo = TemplateRepository(session)
            self.template_variable_repo = TemplateVariableRepository(session)

    def get_session(self) -> Session:
        """获取新的数据库会话

        Returns:
            SQLAlchemy会话对象
        """
        return self.session_factory()

    # -----------------------------------------------------------------------------
    # Epic相关操作
    # -----------------------------------------------------------------------------

    def create_epic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Epic

        Args:
            data: Epic数据

        Returns:
            创建的Epic数据
        """
        with self.session_factory() as session:
            repo = EpicRepository(session)
            epic = repo.create(data)
            return epic.to_dict()

    def get_epic(self, epic_id: str) -> Optional[Dict[str, Any]]:
        """获取Epic

        Args:
            epic_id: Epic ID

        Returns:
            Epic数据或None
        """
        with self.session_factory() as session:
            repo = EpicRepository(session)
            epic = repo.get_by_id(epic_id)
            return epic.to_dict() if epic else None

    def list_epics(self) -> List[Dict[str, Any]]:
        """获取所有Epic

        Returns:
            Epic数据列表
        """
        with self.session_factory() as session:
            repo = EpicRepository(session)
            epics = repo.get_all()
            return [epic.to_dict() for epic in epics]

    def update_epic(self, epic_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新Epic

        Args:
            epic_id: Epic ID
            data: 更新数据

        Returns:
            更新后的Epic数据或None
        """
        with self.session_factory() as session:
            repo = EpicRepository(session)
            epic = repo.update(epic_id, data)
            return epic.to_dict() if epic else None

    def delete_epic(self, epic_id: str) -> bool:
        """删除Epic

        Args:
            epic_id: Epic ID

        Returns:
            是否删除成功
        """
        with self.session_factory() as session:
            repo = EpicRepository(session)
            return repo.delete(epic_id)

    # -----------------------------------------------------------------------------
    # Story相关操作
    # -----------------------------------------------------------------------------

    def create_story(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Story

        Args:
            data: Story数据

        Returns:
            创建的Story数据
        """
        with self.session_factory() as session:
            repo = StoryRepository(session)
            story = repo.create(data)
            return story.to_dict()

    def get_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        """获取Story

        Args:
            story_id: Story ID

        Returns:
            Story数据或None
        """
        with self.session_factory() as session:
            repo = StoryRepository(session)
            story = repo.get_by_id(story_id)
            return story.to_dict() if story else None

    def list_stories(self, epic_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取Stories

        Args:
            epic_id: 可选的Epic ID过滤器

        Returns:
            Story数据列表
        """
        with self.session_factory() as session:
            repo = StoryRepository(session)

            if epic_id:
                stories = repo.get_by_epic(epic_id)
            else:
                stories = repo.get_all()

            return [story.to_dict() for story in stories]

    def update_story(self, story_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新Story

        Args:
            story_id: Story ID
            data: 更新数据

        Returns:
            更新后的Story数据或None
        """
        with self.session_factory() as session:
            repo = StoryRepository(session)
            story = repo.update(story_id, data)
            return story.to_dict() if story else None

    def delete_story(self, story_id: str) -> bool:
        """删除Story

        Args:
            story_id: Story ID

        Returns:
            是否删除成功
        """
        with self.session_factory() as session:
            repo = StoryRepository(session)
            return repo.delete(story_id)

    # -----------------------------------------------------------------------------
    # Task相关操作
    # -----------------------------------------------------------------------------

    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Task

        Args:
            data: Task数据

        Returns:
            创建的Task数据
        """
        with self.session_factory() as session:
            repo = TaskRepository(session)
            task = repo.create(data)
            return task.to_dict()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取Task

        Args:
            task_id: Task ID

        Returns:
            Task数据或None
        """
        with self.session_factory() as session:
            repo = TaskRepository(session)
            task = repo.get_by_id(task_id)
            return task.to_dict() if task else None

    def list_tasks(self, story_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取Tasks

        Args:
            story_id: 可选的Story ID过滤器

        Returns:
            Task数据列表
        """
        with self.session_factory() as session:
            repo = TaskRepository(session)

            if story_id:
                tasks = repo.get_by_story(story_id)
            else:
                tasks = repo.get_all()

            return [task.to_dict() for task in tasks]

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新Task

        Args:
            task_id: Task ID
            data: 更新数据

        Returns:
            更新后的Task数据或None
        """
        with self.session_factory() as session:
            repo = TaskRepository(session)
            task = repo.update(task_id, data)
            return task.to_dict() if task else None

    def delete_task(self, task_id: str) -> bool:
        """删除Task

        Args:
            task_id: Task ID

        Returns:
            是否删除成功
        """
        with self.session_factory() as session:
            repo = TaskRepository(session)
            return repo.delete(task_id)

    # -----------------------------------------------------------------------------
    # Label相关操作
    # -----------------------------------------------------------------------------

    def create_label(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Label

        Args:
            data: Label数据

        Returns:
            创建的Label数据
        """
        with self.session_factory() as session:
            repo = LabelRepository(session)
            label = repo.create(data)
            return label.to_dict()

    def get_label(self, label_id: str) -> Optional[Dict[str, Any]]:
        """获取Label

        Args:
            label_id: Label ID

        Returns:
            Label数据或None
        """
        with self.session_factory() as session:
            repo = LabelRepository(session)
            label = repo.get_by_id(label_id)
            return label.to_dict() if label else None

    def list_labels(self) -> List[Dict[str, Any]]:
        """获取所有Label

        Returns:
            Label数据列表
        """
        with self.session_factory() as session:
            repo = LabelRepository(session)
            labels = repo.get_all()
            return [label.to_dict() for label in labels]

    def update_label(self, label_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新Label

        Args:
            label_id: Label ID
            data: 更新数据

        Returns:
            更新后的Label数据或None
        """
        with self.session_factory() as session:
            repo = LabelRepository(session)
            label = repo.update(label_id, data)
            return label.to_dict() if label else None

    def delete_label(self, label_id: str) -> bool:
        """删除Label

        Args:
            label_id: Label ID

        Returns:
            是否删除成功
        """
        with self.session_factory() as session:
            repo = LabelRepository(session)
            return repo.delete(label_id)

    # -----------------------------------------------------------------------------
    # Template相关操作
    # -----------------------------------------------------------------------------

    def create_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Template

        Args:
            data: Template数据

        Returns:
            创建的Template数据
        """
        with self.session_factory() as session:
            repo = TemplateRepository(session)
            template = repo.create(data)
            return template.to_dict()

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """获取Template

        Args:
            template_id: Template ID

        Returns:
            Template数据或None
        """
        with self.session_factory() as session:
            repo = TemplateRepository(session)
            template = repo.get_by_id(template_id)
            return template.to_dict() if template else None

    def get_template_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """通过名称获取Template

        Args:
            name: Template名称

        Returns:
            Template数据或None
        """
        with self.session_factory() as session:
            repo = TemplateRepository(session)
            template = repo.get_by_name(name)
            return template.to_dict() if template else None

    def list_templates(self) -> List[Dict[str, Any]]:
        """获取所有Template

        Returns:
            Template数据列表
        """
        with self.session_factory() as session:
            repo = TemplateRepository(session)
            templates = repo.get_all()
            return [template.to_dict() for template in templates]

    def search_templates(
        self, query: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """搜索Template

        Args:
            query: 搜索关键词
            tags: 标签列表

        Returns:
            匹配的Template数据列表
        """
        with self.session_factory() as session:
            repo = TemplateRepository(session)
            templates = repo.search(query, tags)
            return [template.to_dict() for template in templates]

    def update_template(self, template_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新Template

        Args:
            template_id: Template ID
            data: 更新数据

        Returns:
            更新后的Template数据或None
        """
        with self.session_factory() as session:
            repo = TemplateRepository(session)
            template = repo.update(template_id, data)
            return template.to_dict() if template else None

    def delete_template(self, template_id: str) -> bool:
        """删除Template

        Args:
            template_id: Template ID

        Returns:
            是否删除成功
        """
        with self.session_factory() as session:
            repo = TemplateRepository(session)
            return repo.delete(template_id)

    # -----------------------------------------------------------------------------
    # TemplateVariable相关操作
    # -----------------------------------------------------------------------------

    def get_template_variable(self, variable_id: str) -> Optional[Dict[str, Any]]:
        """获取TemplateVariable

        Args:
            variable_id: TemplateVariable ID

        Returns:
            TemplateVariable数据或None
        """
        with self.session_factory() as session:
            repo = TemplateVariableRepository(session)
            variable = repo.get_by_id(variable_id)
            return variable.to_dict() if variable else None

    def list_template_variables(self, template_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取TemplateVariables

        Args:
            template_id: 可选的Template ID过滤器

        Returns:
            TemplateVariable数据列表
        """
        with self.session_factory() as session:
            repo = TemplateVariableRepository(session)

            if template_id:
                variables = repo.get_by_template(template_id)
            else:
                variables = repo.get_all()

            return [variable.to_dict() for variable in variables]
