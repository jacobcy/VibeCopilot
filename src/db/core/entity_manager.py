"""
实体管理器模块

提供通用的实体管理功能。
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EntityManager:
    """实体管理器

    提供通用的实体CRUD操作接口。
    """

    def __init__(self, repo_map: Dict[str, Any], mock_storage=None):
        """初始化实体管理器

        Args:
            repo_map: 类型到仓库的映射
            mock_storage: 模拟存储对象
        """
        self._repo_map = repo_map
        self._mock_storage = mock_storage

    def get_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """通用获取实体方法

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            实体数据
        """
        if entity_type == "task" and entity_type in self._repo_map:
            # Task已经是SQLAlchemy模型，直接使用仓库
            entity = self._repo_map[entity_type].get_by_id(entity_id)
            if not entity:
                return None
            return entity.to_dict() if hasattr(entity, "to_dict") else vars(entity)
        elif entity_type in ["epic", "story", "label", "template"] and self._mock_storage:
            # 其他类型使用模拟存储
            return self._mock_storage.get_entity(entity_type, entity_id)
        else:
            logger.warning(f"未知实体类型: {entity_type}")
            return None

    def get_entities(self, entity_type: str) -> List[Dict[str, Any]]:
        """通用获取实体列表方法

        Args:
            entity_type: 实体类型

        Returns:
            实体列表
        """
        if entity_type == "task" and entity_type in self._repo_map:
            # Task已经是SQLAlchemy模型，直接使用仓库
            entities = self._repo_map[entity_type].get_all()
            return [
                entity.to_dict() if hasattr(entity, "to_dict") else vars(entity)
                for entity in entities
            ]
        elif entity_type in ["epic", "story", "label", "template"] and self._mock_storage:
            # 其他类型使用模拟存储
            return self._mock_storage.get_entities(entity_type)
        else:
            logger.warning(f"未知实体类型: {entity_type}")
            return []

    def create_entity(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通用创建实体方法

        Args:
            entity_type: 实体类型
            data: 实体数据

        Returns:
            创建的实体
        """
        logger.info(f"创建实体 {entity_type}，数据: {data}")

        if entity_type == "task" and entity_type in self._repo_map:
            # Task已经是SQLAlchemy模型，直接使用仓库
            logger.info(f"使用TaskRepository创建Task")

            # 检查必要字段
            missing_fields = []
            for field in ["id", "title"]:
                if field not in data:
                    missing_fields.append(field)

            if missing_fields:
                err_msg = f"创建Task缺少必要字段: {', '.join(missing_fields)}"
                logger.error(err_msg)
                raise ValueError(err_msg)

            entity = self._repo_map[entity_type].create(data)
            return entity.to_dict() if hasattr(entity, "to_dict") else vars(entity)
        elif entity_type in ["epic", "story", "label", "template"] and self._mock_storage:
            # 其他类型使用模拟存储
            return self._mock_storage.create_entity(entity_type, data)
        else:
            logger.warning(f"未知实体类型: {entity_type}")
            return data

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
        if entity_type == "task" and entity_type in self._repo_map:
            # Task已经是SQLAlchemy模型，直接使用仓库
            entity = self._repo_map[entity_type].update(entity_id, data)
            if not entity:
                return None
            return entity.to_dict() if hasattr(entity, "to_dict") else vars(entity)
        elif entity_type in ["epic", "story", "label", "template"] and self._mock_storage:
            # 其他类型使用模拟存储
            return self._mock_storage.update_entity(entity_type, entity_id, data)
        else:
            logger.warning(f"未知实体类型: {entity_type}")
            return None

    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """通用删除实体方法

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            是否成功
        """
        if entity_type == "task" and entity_type in self._repo_map:
            # Task已经是SQLAlchemy模型，直接使用仓库
            return self._repo_map[entity_type].delete(entity_id)
        elif entity_type in ["epic", "story", "label", "template"] and self._mock_storage:
            # 其他类型使用模拟存储
            return self._mock_storage.delete_entity(entity_type, entity_id)
        else:
            logger.warning(f"未知实体类型: {entity_type}")
            return False

    def search_entities(self, entity_type: str, query: str) -> List[Dict[str, Any]]:
        """通用搜索实体方法

        Args:
            entity_type: 实体类型
            query: 搜索关键词

        Returns:
            匹配的实体列表
        """
        # 获取所有实体
        entities = self.get_entities(entity_type)
        if not entities:
            return []

        # 简单过滤
        query = query.lower()
        return [
            entity
            for entity in entities
            if query in entity.get("title", "").lower()
            or query in entity.get("description", "").lower()
        ]
