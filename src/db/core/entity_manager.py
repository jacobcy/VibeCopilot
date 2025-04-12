"""
实体管理器模块

提供统一的实体管理接口，整合各种仓库。
"""

import logging
from typing import Any, Dict, List, Optional

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

    def get_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """通用获取实体方法

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            实体数据
        """
        if entity_type not in self.repositories:
            logger.warning(f"未找到 {entity_type} 类型的仓库")
            return None

        # 所有实体统一使用仓库
        entity = self.repositories[entity_type].get_by_id(entity_id)
        if not entity:
            return None

        # 转换为字典
        if hasattr(entity, "to_dict"):
            return entity.to_dict()
        else:
            # 手动转换实体为字典
            try:
                if hasattr(entity, "__table__"):
                    # SQLAlchemy模型
                    entity_dict = {}
                    for column in entity.__table__.columns:
                        column_name = column.name
                        entity_dict[column_name] = getattr(entity, column_name)
                    return entity_dict
                else:
                    # 尝试使用vars()
                    return vars(entity)
            except Exception as e:
                logger.error(f"转换实体为字典失败: {e}")
                return None

    def get_entities(self, entity_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的所有实体

        Args:
            entity_type: 实体类型

        Returns:
            实体列表
        """
        try:
            logger.debug(f"尝试获取 {entity_type} 类型的所有实体")

            # 检查仓库是否存在
            if entity_type not in self.repositories:
                logger.warning(f"未找到 {entity_type} 类型的仓库")
                return []

            # 使用对应的仓库
            repository = self.repositories[entity_type]
            if hasattr(repository, "get_all"):
                # 获取所有实体
                entity_objects = repository.get_all()

                # 转换为字典列表
                entities = []
                for entity in entity_objects:
                    if hasattr(entity, "to_dict"):
                        entities.append(entity.to_dict())
                    elif hasattr(entity, "__table__"):
                        # SQLAlchemy模型
                        entity_dict = {}
                        for column in entity.__table__.columns:
                            column_name = column.name
                            entity_dict[column_name] = getattr(entity, column_name)
                        entities.append(entity_dict)
                    else:
                        # 尝试使用vars()
                        entities.append(vars(entity))

                logger.debug(f"从 {entity_type} 仓库获取到 {len(entities)} 个实体")
                return entities
            else:
                logger.warning(f"{entity_type} 仓库缺少 get_all 方法")
                return []
        except Exception as e:
            logger.error(f"获取 {entity_type} 实体列表失败: {e}", exc_info=True)
            # 不抛出异常，返回空列表
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

        if entity_type not in self.repositories:
            logger.warning(f"未找到 {entity_type} 类型的仓库")
            return data

        # 所有实体类型都使用仓库创建
        try:
            entity = self.repositories[entity_type].create(data)

            # 转换为字典返回
            if hasattr(entity, "to_dict"):
                return entity.to_dict()
            elif hasattr(entity, "__table__"):
                # SQLAlchemy模型
                entity_dict = {}
                for column in entity.__table__.columns:
                    column_name = column.name
                    entity_dict[column_name] = getattr(entity, column_name)
                return entity_dict
            else:
                # 尝试使用vars()
                return vars(entity)
        except Exception as e:
            logger.error(f"创建 {entity_type} 实体失败: {e}", exc_info=True)
            raise

    def update_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通用更新实体方法

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            data: 更新数据

        Returns:
            更新后的实体
        """
        if entity_type not in self.repositories:
            logger.warning(f"未找到 {entity_type} 类型的仓库")
            return None

        # 所有实体类型都使用仓库更新
        entity = self.repositories[entity_type].update(entity_id, data)
        if not entity:
            return None

        # 转换为字典返回
        if hasattr(entity, "to_dict"):
            return entity.to_dict()
        elif hasattr(entity, "__table__"):
            # SQLAlchemy模型
            entity_dict = {}
            for column in entity.__table__.columns:
                column_name = column.name
                entity_dict[column_name] = getattr(entity, column_name)
            return entity_dict
        else:
            # 尝试使用vars()
            return vars(entity)

    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """通用删除实体方法

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            是否成功
        """
        if entity_type not in self.repositories:
            logger.warning(f"未找到 {entity_type} 类型的仓库")
            return False

        # 所有实体类型都使用仓库删除
        return self.repositories[entity_type].delete(entity_id)

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
        return [entity for entity in entities if query in entity.get("title", "").lower() or query in entity.get("description", "").lower()]
