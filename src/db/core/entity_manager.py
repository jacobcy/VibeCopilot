"""
实体管理器模块

提供统一的实体管理接口，整合各种仓库。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EntityManager:
    """实体管理器，整合不同的仓库，提供统一接口"""

    def __init__(self, repositories: Dict):
        """初始化实体管理器

        Args:
            repositories: 仓库字典，键为实体类型，值为仓库对象
        """
        self.repositories = repositories
        logger.debug(f"实体管理器初始化，管理 {len(repositories)} 个仓库")

    def get_entity(self, session: Session, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """通用获取实体方法

        Args:
            session: SQLAlchemy 会话对象
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            实体数据字典或None
        """
        if entity_type not in self.repositories:
            logger.warning(f"未找到 {entity_type} 类型的仓库")
            return None

        repository = self.repositories[entity_type]
        entity = repository.get_by_id(session, entity_id)
        if not entity:
            return None

        try:
            if hasattr(entity, "to_dict") and callable(entity.to_dict):
                return entity.to_dict()
            elif hasattr(entity, "__table__"):
                entity_dict = {}
                for column in entity.__table__.columns:
                    entity_dict[column.name] = getattr(entity, column.name)
                return entity_dict
            else:
                return vars(entity)
        except Exception as e:
            logger.error(f"将实体 {entity_type} (ID: {entity_id}) 转换为字典失败: {e}", exc_info=True)
            return None

    def get_entities(self, session: Session, entity_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的所有实体

        Args:
            session: SQLAlchemy 会话对象
            entity_type: 实体类型

        Returns:
            实体字典列表
        """
        try:
            logger.debug(f"尝试获取 {entity_type} 类型的所有实体")

            if entity_type not in self.repositories:
                logger.warning(f"未找到 {entity_type} 类型的仓库")
                return []

            repository = self.repositories[entity_type]
            if hasattr(repository, "get_all"):
                entity_objects = repository.get_all(session)

                entities = []
                for entity in entity_objects:
                    try:
                        if hasattr(entity, "to_dict") and callable(entity.to_dict):
                            entities.append(entity.to_dict())
                        elif hasattr(entity, "__table__"):
                            entity_dict = {}
                            for column in entity.__table__.columns:
                                entity_dict[column.name] = getattr(entity, column.name)
                            entities.append(entity_dict)
                        else:
                            entities.append(vars(entity))
                    except Exception as e:
                        entity_id_str = getattr(entity, "id", "未知ID")
                        logger.error(f"将实体 {entity_type} (ID: {entity_id_str}) 转换为字典失败: {e}", exc_info=True)

                logger.debug(f"从 {entity_type} 仓库获取到 {len(entities)} 个实体")
                return entities
            else:
                logger.warning(f"{entity_type} 仓库缺少 get_all 方法")
                return []
        except Exception as e:
            logger.error(f"获取 {entity_type} 实体列表失败: {e}", exc_info=True)
            return []

    def create_entity(self, session: Session, entity_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """通用创建实体方法

        Args:
            session: SQLAlchemy 会话对象
            entity_type: 实体类型
            data: 实体数据

        Returns:
            创建的实体字典或None
        """
        logger.info(f"创建实体 {entity_type}")
        if entity_type not in self.repositories:
            logger.warning(f"未找到 {entity_type} 类型的仓库")
            return None

        repository = self.repositories[entity_type]
        try:
            entity = repository.create(session, data)
            if not entity:
                logger.error(f"创建 {entity_type} 实体失败，仓库返回None")
                return None

            if hasattr(entity, "to_dict") and callable(entity.to_dict):
                return entity.to_dict()
            elif hasattr(entity, "__table__"):
                entity_dict = {}
                for column in entity.__table__.columns:
                    entity_dict[column.name] = getattr(entity, column.name)
                return entity_dict
            else:
                return vars(entity)
        except Exception as e:
            logger.error(f"创建 {entity_type} 实体失败: {e}", exc_info=True)
            return None

    def update_entity(self, session: Session, entity_type: str, entity_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """通用更新实体方法

        Args:
            session: SQLAlchemy 会话对象
            entity_type: 实体类型
            entity_id: 实体ID
            data: 更新数据

        Returns:
            更新后的实体字典或None
        """
        if entity_type not in self.repositories:
            logger.warning(f"未找到 {entity_type} 类型的仓库")
            return None

        repository = self.repositories[entity_type]
        try:
            entity = repository.update(session, entity_id, data)
            if not entity:
                return None

            if hasattr(entity, "to_dict") and callable(entity.to_dict):
                return entity.to_dict()
            elif hasattr(entity, "__table__"):
                entity_dict = {}
                for column in entity.__table__.columns:
                    entity_dict[column.name] = getattr(entity, column.name)
                return entity_dict
            else:
                return vars(entity)
        except Exception as e:
            logger.error(f"更新实体 {entity_type} (ID: {entity_id}) 失败: {e}", exc_info=True)
            return None

    def delete_entity(self, session: Session, entity_type: str, entity_id: str) -> bool:
        """通用删除实体方法

        Args:
            session: SQLAlchemy 会话对象
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            是否成功
        """
        if entity_type not in self.repositories:
            logger.warning(f"未找到 {entity_type} 类型的仓库")
            return False

        repository = self.repositories[entity_type]
        try:
            return repository.delete(session, entity_id)
        except Exception as e:
            logger.error(f"删除实体 {entity_type} (ID: {entity_id}) 失败: {e}", exc_info=True)
            return False

    def search_entities(self, session: Session, entity_type: str, query: str) -> List[Dict[str, Any]]:
        """通用搜索实体方法

        Args:
            session: SQLAlchemy 会话对象
            entity_type: 实体类型
            query: 搜索关键词

        Returns:
            匹配的实体字典列表
        """
        entities = self.get_entities(session, entity_type)
        if not entities:
            return []

        query_lower = query.lower()
        results = []
        for entity_dict in entities:
            title = str(entity_dict.get("title", "")).lower()
            description = str(entity_dict.get("description", "")).lower()
            if query_lower in title or query_lower in description:
                results.append(entity_dict)
        return results
