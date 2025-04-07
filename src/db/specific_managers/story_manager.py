"""
Story管理器模块

提供Story实体的管理功能。
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StoryManager:
    """Story管理器

    提供Story实体的管理功能。
    """

    def __init__(self, entity_manager, mock_storage):
        """初始化Story管理器

        Args:
            entity_manager: 实体管理器
            mock_storage: 模拟存储
        """
        self._entity_manager = entity_manager
        self._mock_storage = mock_storage

    def get_story(self, story_id: str) -> Dict[str, Any]:
        """获取Story信息

        Args:
            story_id: Story ID

        Returns:
            Story信息
        """
        return self._entity_manager.get_entity("story", story_id)

    def list_stories(self) -> List[Dict[str, Any]]:
        """获取所有Story

        Returns:
            Story列表
        """
        return self._entity_manager.get_entities("story")

    def create_story(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Story

        Args:
            data: Story数据

        Returns:
            创建的Story
        """
        return self._entity_manager.create_entity("story", data)

    def update_story(self, story_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Story

        Args:
            story_id: Story ID
            data: 更新数据

        Returns:
            更新后的Story
        """
        return self._entity_manager.update_entity("story", story_id, data)

    def delete_story(self, story_id: str) -> bool:
        """删除Story

        Args:
            story_id: Story ID

        Returns:
            是否成功
        """
        return self._entity_manager.delete_entity("story", story_id)
