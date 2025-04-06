"""
数据库服务模块

提供统一的数据库服务接口，集成各Repository对象。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import (
    EpicRepository,
    StoryRepository,
    TaskRepository,
    get_engine,
    get_session_factory,
    init_db,
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """数据库服务类，整合各Repository提供统一接口"""

    def __init__(self):
        """初始化数据库服务"""
        # 初始化数据库
        engine = init_db()
        session_factory = get_session_factory(engine)
        self.session = session_factory()

        # 初始化各个仓库
        self.epic_repo = EpicRepository(self.session)
        self.story_repo = StoryRepository(self.session)
        self.task_repo = TaskRepository(self.session)

    def get_epic(self, epic_id: str) -> Dict[str, Any]:
        """获取Epic信息"""
        epic = self.epic_repo.get_by_id(epic_id)
        if not epic:
            return None
        return epic.to_dict() if hasattr(epic, "to_dict") else vars(epic)

    def get_story(self, story_id: str) -> Dict[str, Any]:
        """获取Story信息"""
        story = self.story_repo.get_by_id(story_id)
        if not story:
            return None
        return story.to_dict() if hasattr(story, "to_dict") else vars(story)

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """获取Task信息"""
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return None
        return task.to_dict() if hasattr(task, "to_dict") else vars(task)

    def get_label(self, label_id: str) -> Dict[str, Any]:
        """获取Label信息"""
        # 暂未实现，返回空数据
        return {"id": label_id, "name": "占位标签"}

    def get_template(self, template_id: str) -> Dict[str, Any]:
        """获取Template信息"""
        # 暂未实现，返回空数据
        return {"id": template_id, "name": "占位模板"}

    def list_epics(self) -> List[Dict[str, Any]]:
        """获取所有Epic"""
        epics = self.epic_repo.get_all()
        return [epic.to_dict() if hasattr(epic, "to_dict") else vars(epic) for epic in epics]

    def list_stories(self) -> List[Dict[str, Any]]:
        """获取所有Story"""
        stories = self.story_repo.get_all()
        return [story.to_dict() if hasattr(story, "to_dict") else vars(story) for story in stories]

    def list_tasks(self) -> List[Dict[str, Any]]:
        """获取所有Task"""
        tasks = self.task_repo.get_all()
        return [task.to_dict() if hasattr(task, "to_dict") else vars(task) for task in tasks]

    def list_labels(self) -> List[Dict[str, Any]]:
        """获取所有Label"""
        # 暂未实现，返回空列表
        return []

    def list_templates(self) -> List[Dict[str, Any]]:
        """获取所有Template"""
        # 暂未实现，返回空列表
        return []

    def search_templates(self, query: str, tags=None) -> List[Dict[str, Any]]:
        """搜索模板"""
        # 暂未实现，返回空列表
        return []

    def create_epic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Epic"""
        epic = self.epic_repo.create(data)
        return epic.to_dict() if hasattr(epic, "to_dict") else vars(epic)

    def create_story(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Story"""
        story = self.story_repo.create(data)
        return story.to_dict() if hasattr(story, "to_dict") else vars(story)

    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Task"""
        task = self.task_repo.create(data)
        return task.to_dict() if hasattr(task, "to_dict") else vars(task)

    def create_label(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Label"""
        # 暂未实现，返回原始数据
        return data

    def create_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Template"""
        # 暂未实现，返回原始数据
        return data

    def update_epic(self, epic_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Epic"""
        epic = self.epic_repo.update(epic_id, data)
        if not epic:
            return None
        return epic.to_dict() if hasattr(epic, "to_dict") else vars(epic)

    def update_story(self, story_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Story"""
        story = self.story_repo.update(story_id, data)
        if not story:
            return None
        return story.to_dict() if hasattr(story, "to_dict") else vars(story)

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Task"""
        task = self.task_repo.update(task_id, data)
        if not task:
            return None
        return task.to_dict() if hasattr(task, "to_dict") else vars(task)

    def update_label(self, label_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Label"""
        # 暂未实现，返回原始数据
        return data

    def update_template(self, template_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Template"""
        # 暂未实现，返回原始数据
        return data

    def delete_epic(self, epic_id: str) -> bool:
        """删除Epic"""
        return self.epic_repo.delete(epic_id)

    def delete_story(self, story_id: str) -> bool:
        """删除Story"""
        return self.story_repo.delete(story_id)

    def delete_task(self, task_id: str) -> bool:
        """删除Task"""
        return self.task_repo.delete(task_id)

    def delete_label(self, label_id: str) -> bool:
        """删除Label"""
        # 暂未实现，假设成功
        return True

    def delete_template(self, template_id: str) -> bool:
        """删除Template"""
        # 暂未实现，假设成功
        return True
