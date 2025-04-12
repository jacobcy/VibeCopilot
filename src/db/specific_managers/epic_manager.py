"""
Epic管理器模块

提供Epic实体的管理功能。
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EpicManager:
    """Epic管理器

    提供Epic实体的管理功能。
    """

    def __init__(self, entity_manager):
        """初始化Epic管理器

        Args:
            entity_manager: 实体管理器
        """
        self._entity_manager = entity_manager

    def get_epic(self, epic_id: str) -> Dict[str, Any]:
        """获取Epic信息

        Args:
            epic_id: Epic ID

        Returns:
            Epic信息
        """
        return self._entity_manager.get_entity("epic", epic_id)

    def list_epics(self) -> List[Dict[str, Any]]:
        """获取所有Epic

        Returns:
            Epic列表
        """
        logger.info("获取所有Epic列表")
        try:
            # 直接使用实体管理器获取Epic列表
            epics = self._entity_manager.get_entities("epic")
            logger.info(f"获取到 {len(epics)} 个Epic")
            return epics
        except Exception as e:
            logger.error(f"获取Epic列表失败: {e}", exc_info=True)
            # 不要抛出异常，返回空列表
            return []

    def create_epic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Epic

        Args:
            data: Epic数据

        Returns:
            创建的Epic
        """
        return self._entity_manager.create_entity("epic", data)

    def update_epic(self, epic_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Epic

        Args:
            epic_id: Epic ID
            data: 更新数据

        Returns:
            更新后的Epic
        """
        return self._entity_manager.update_entity("epic", epic_id, data)

    def delete_epic(self, epic_id: str) -> bool:
        """删除Epic

        Args:
            epic_id: Epic ID

        Returns:
            是否成功
        """
        return self._entity_manager.delete_entity("epic", epic_id)
