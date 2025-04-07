"""
数据库服务模块

提供统一的数据库服务接口，集成各Repository对象。
"""

import logging
from typing import Any, Dict, List, Optional

# 导入上层模块定义的数据库函数
from src.db import get_engine, get_session_factory
from src.db.core.entity_manager import EntityManager
from src.db.core.mock_storage import MockStorage
from src.db.repositories.roadmap_repository import EpicRepository, StoryRepository, TaskRepository
from src.db.specific_managers.epic_manager import EpicManager
from src.db.specific_managers.story_manager import StoryManager
from src.db.specific_managers.task_manager import TaskManager

# 直接从各自的模块导入
from src.models.db.init_db import init_db

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

        # 类型到仓库的映射
        self.repo_map = {
            "epic": self.epic_repo,
            "story": self.story_repo,
            "task": self.task_repo,
        }

        # 初始化模拟存储
        self.mock_storage = MockStorage()

        # 初始化实体管理器
        self.entity_manager = EntityManager(self.repo_map, self.mock_storage)

        # 初始化特定实体管理器
        self.epic_manager = EpicManager(self.entity_manager, self.mock_storage)
        self.story_manager = StoryManager(self.entity_manager, self.mock_storage)
        self.task_manager = TaskManager(self.entity_manager, self.task_repo)

    # 通用实体管理方法，委托给实体管理器

    def get_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """通用获取实体方法

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            实体数据
        """
        return self.entity_manager.get_entity(entity_type, entity_id)

    def get_entities(self, entity_type: str) -> List[Dict[str, Any]]:
        """通用获取实体列表方法

        Args:
            entity_type: 实体类型

        Returns:
            实体列表
        """
        return self.entity_manager.get_entities(entity_type)

    def create_entity(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通用创建实体方法

        Args:
            entity_type: 实体类型
            data: 实体数据

        Returns:
            创建的实体
        """
        return self.entity_manager.create_entity(entity_type, data)

    def update_entity(
        self, entity_type: str, entity_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """通用更新实体方法

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            data: 更新数据

        Returns:
            更新后的实体
        """
        return self.entity_manager.update_entity(entity_type, entity_id, data)

    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """通用删除实体方法

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            是否成功
        """
        return self.entity_manager.delete_entity(entity_type, entity_id)

    def search_entities(self, entity_type: str, query: str) -> List[Dict[str, Any]]:
        """通用搜索实体方法

        Args:
            entity_type: 实体类型
            query: 搜索关键词

        Returns:
            匹配的实体列表
        """
        return self.entity_manager.search_entities(entity_type, query)

    # Epic相关方法，委托给Epic管理器

    def get_epic(self, epic_id: str) -> Dict[str, Any]:
        """获取Epic信息"""
        return self.epic_manager.get_epic(epic_id)

    def list_epics(self) -> List[Dict[str, Any]]:
        """获取所有Epic"""
        return self.epic_manager.list_epics()

    def create_epic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Epic"""
        return self.epic_manager.create_epic(data)

    def update_epic(self, epic_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Epic"""
        return self.epic_manager.update_epic(epic_id, data)

    def delete_epic(self, epic_id: str) -> bool:
        """删除Epic"""
        return self.epic_manager.delete_epic(epic_id)

    # Story相关方法，委托给Story管理器

    def get_story(self, story_id: str) -> Dict[str, Any]:
        """获取Story信息"""
        return self.story_manager.get_story(story_id)

    def list_stories(self) -> List[Dict[str, Any]]:
        """获取所有Story"""
        return self.story_manager.list_stories()

    def create_story(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Story"""
        return self.story_manager.create_story(data)

    def update_story(self, story_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Story"""
        return self.story_manager.update_story(story_id, data)

    def delete_story(self, story_id: str) -> bool:
        """删除Story"""
        return self.story_manager.delete_story(story_id)

    # Task相关方法，委托给Task管理器

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """获取Task信息"""
        return self.task_manager.get_task(task_id)

    def list_tasks(self) -> List[Dict[str, Any]]:
        """获取所有Task"""
        return self.task_manager.list_tasks()

    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Task"""
        return self.task_manager.create_task(data)

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Task"""
        return self.task_manager.update_task(task_id, data)

    def delete_task(self, task_id: str) -> bool:
        """删除Task"""
        return self.task_manager.delete_task(task_id)

    # 其他特定实体类型方法

    def get_label(self, label_id: str) -> Dict[str, Any]:
        """获取Label信息"""
        return self.get_entity("label", label_id)

    def get_template(self, template_id: str) -> Dict[str, Any]:
        """获取Template信息"""
        return self.get_entity("template", template_id)

    def list_labels(self) -> List[Dict[str, Any]]:
        """获取所有Label"""
        return self.get_entities("label")

    def list_templates(self) -> List[Dict[str, Any]]:
        """获取所有Template"""
        return self.get_entities("template")

    def search_templates(self, query: str, tags=None) -> List[Dict[str, Any]]:
        """搜索模板"""
        return self.search_entities("template", query)

    def create_label(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Label"""
        return self.create_entity("label", data)

    def create_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Template"""
        return self.create_entity("template", data)

    def update_label(self, label_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Label"""
        return self.update_entity("label", label_id, data)

    def update_template(self, template_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Template"""
        return self.update_entity("template", template_id, data)

    def delete_label(self, label_id: str) -> bool:
        """删除Label"""
        return self.delete_entity("label", label_id)

    def delete_template(self, template_id: str) -> bool:
        """删除Template"""
        return self.delete_entity("template", template_id)
