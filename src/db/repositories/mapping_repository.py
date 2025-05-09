"""
实体映射仓库模块

提供对EntityMapping表的CRUD操作，处理本地实体与远程后端的映射关系
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.models.db.mapping import BackendType, EntityMapping, EntityType

logger = logging.getLogger(__name__)


class EntityMappingRepository:
    """
    实体映射仓库

    处理本地实体（Epic, Story, Task等）与远程后端（GitHub, Linear等）的映射关系
    """

    def create_mapping(
        self,
        session: Session,
        local_entity_id: str,
        local_entity_type: str,
        backend_type: str,
        remote_entity_id: Optional[str] = None,
        remote_entity_number: Optional[str] = None,
        local_project_id: Optional[str] = None,
        remote_project_id: Optional[str] = None,
        remote_project_context: Optional[str] = None,
        sync_data: Optional[Dict[str, Any]] = None,
    ) -> EntityMapping:
        """
        创建新的实体映射

        Args:
            session: 数据库会话
            local_entity_id: 本地实体ID
            local_entity_type: 本地实体类型，如 "roadmap", "epic", "story", "task"
            backend_type: 后端类型，如 "github", "linear"
            remote_entity_id: 远程实体ID，如GitHub Issue ID
            remote_entity_number: 远程实体编号，如GitHub Issue Number
            local_project_id: 本地项目ID，通常是roadmap_id
            remote_project_id: 远程项目ID，如GitHub Project ID
            remote_project_context: 远程项目上下文，如GitHub项目名称
            sync_data: 同步相关的元数据

        Returns:
            EntityMapping: 新创建的映射对象
        """
        try:
            # 检查映射是否已存在
            existing_mapping = self.get_mapping_by_local_id(session, local_entity_id, local_entity_type, backend_type)
            if existing_mapping:
                # 更新现有映射
                if remote_entity_id is not None:
                    existing_mapping.remote_entity_id = remote_entity_id
                if remote_entity_number is not None:
                    existing_mapping.remote_entity_number = remote_entity_number
                if local_project_id is not None:
                    existing_mapping.local_project_id = local_project_id
                if remote_project_id is not None:
                    existing_mapping.remote_project_id = remote_project_id
                if remote_project_context is not None:
                    existing_mapping.remote_project_context = remote_project_context
                if sync_data is not None:
                    existing_mapping.sync_data = sync_data

                existing_mapping.last_synced_at = datetime.utcnow()
                existing_mapping.updated_at = datetime.utcnow()

                session.commit()
                logger.info(f"更新实体映射: {existing_mapping}")
                return existing_mapping

            # 转换为枚举类型
            entity_type_enum = EntityType(local_entity_type)
            backend_type_enum = BackendType(backend_type)

            # 创建新映射
            mapping = EntityMapping(
                id=f"map_{uuid.uuid4().hex[:8]}",
                local_entity_id=local_entity_id,
                local_entity_type=entity_type_enum,
                backend_type=backend_type_enum,
                remote_entity_id=remote_entity_id,
                remote_entity_number=remote_entity_number,
                local_project_id=local_project_id,
                remote_project_id=remote_project_id,
                remote_project_context=remote_project_context,
                last_synced_at=datetime.utcnow(),
                sync_data=sync_data,
            )

            session.add(mapping)
            session.commit()
            logger.info(f"创建实体映射: {mapping}")
            return mapping

        except Exception as e:
            session.rollback()
            logger.error(f"创建实体映射时出错: {e}", exc_info=True)
            raise

    def get_mapping_by_local_id(self, session: Session, local_entity_id: str, local_entity_type: str, backend_type: str) -> Optional[EntityMapping]:
        """
        根据本地实体ID和类型获取映射

        Args:
            session: 数据库会话
            local_entity_id: 本地实体ID
            local_entity_type: 本地实体类型，如 "roadmap", "epic", "story", "task"
            backend_type: 后端类型，如 "github", "linear"

        Returns:
            Optional[EntityMapping]: 找到的映射，或None
        """
        try:
            # 转换为枚举类型
            entity_type_enum = EntityType(local_entity_type)
            backend_type_enum = BackendType(backend_type)

            return (
                session.query(EntityMapping)
                .filter(
                    EntityMapping.local_entity_id == local_entity_id,
                    EntityMapping.local_entity_type == entity_type_enum,
                    EntityMapping.backend_type == backend_type_enum,
                )
                .first()
            )

        except Exception as e:
            logger.error(f"获取实体映射时出错: {e}", exc_info=True)
            return None

    def get_mapping_by_remote_id(self, session: Session, remote_entity_id: str, backend_type: str) -> Optional[EntityMapping]:
        """
        根据远程实体ID获取映射

        Args:
            session: 数据库会话
            remote_entity_id: 远程实体ID
            backend_type: 后端类型，如 "github", "linear"

        Returns:
            Optional[EntityMapping]: 找到的映射，或None
        """
        try:
            # 转换为枚举类型
            backend_type_enum = BackendType(backend_type)

            return (
                session.query(EntityMapping)
                .filter(EntityMapping.remote_entity_id == remote_entity_id, EntityMapping.backend_type == backend_type_enum)
                .first()
            )

        except Exception as e:
            logger.error(f"获取实体映射时出错: {e}", exc_info=True)
            return None

    def get_mapping_by_remote_number(
        self, session: Session, remote_entity_number: str, local_entity_type: str, backend_type: str, remote_project_id: Optional[str] = None
    ) -> Optional[EntityMapping]:
        """
        根据远程实体编号获取映射

        Args:
            session: 数据库会话
            remote_entity_number: 远程实体编号，如GitHub Issue Number
            local_entity_type: 本地实体类型，用于过滤
            backend_type: 后端类型，如 "github", "linear"
            remote_project_id: 远程项目ID，用于确保唯一性

        Returns:
            Optional[EntityMapping]: 找到的映射，或None
        """
        try:
            # 转换为枚举类型
            entity_type_enum = EntityType(local_entity_type)
            backend_type_enum = BackendType(backend_type)

            query = session.query(EntityMapping).filter(
                EntityMapping.remote_entity_number == remote_entity_number,
                EntityMapping.local_entity_type == entity_type_enum,
                EntityMapping.backend_type == backend_type_enum,
            )

            # 如果提供了项目ID，则添加过滤条件
            if remote_project_id:
                query = query.filter(EntityMapping.remote_project_id == remote_project_id)

            return query.first()

        except Exception as e:
            logger.error(f"获取实体映射时出错: {e}", exc_info=True)
            return None

    def update_mapping(self, session: Session, mapping_id: str, **kwargs) -> Optional[EntityMapping]:
        """
        更新实体映射

        Args:
            session: 数据库会话
            mapping_id: 映射ID
            **kwargs: 要更新的字段

        Returns:
            Optional[EntityMapping]: 更新后的映射，或None
        """
        try:
            mapping = session.query(EntityMapping).filter(EntityMapping.id == mapping_id).first()
            if not mapping:
                logger.warning(f"未找到映射: {mapping_id}")
                return None

            # 更新字段
            for key, value in kwargs.items():
                if hasattr(mapping, key):
                    setattr(mapping, key, value)

            # 更新时间戳
            mapping.updated_at = datetime.utcnow()
            if "remote_entity_id" in kwargs or "remote_entity_number" in kwargs:
                mapping.last_synced_at = datetime.utcnow()

            session.commit()
            logger.info(f"更新实体映射: {mapping}")
            return mapping

        except Exception as e:
            session.rollback()
            logger.error(f"更新实体映射时出错: {e}", exc_info=True)
            return None

    def delete_mapping(self, session: Session, mapping_id: str) -> bool:
        """
        删除实体映射

        Args:
            session: 数据库会话
            mapping_id: 映射ID

        Returns:
            bool: 操作是否成功
        """
        try:
            mapping = session.query(EntityMapping).filter(EntityMapping.id == mapping_id).first()
            if not mapping:
                logger.warning(f"未找到映射: {mapping_id}")
                return False

            session.delete(mapping)
            session.commit()
            logger.info(f"删除实体映射: {mapping_id}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"删除实体映射时出错: {e}", exc_info=True)
            return False

    def get_mappings_by_project(
        self, session: Session, local_project_id: str, entity_type: Optional[str] = None, backend_type: Optional[str] = None
    ) -> List[EntityMapping]:
        """
        获取指定项目的所有映射

        Args:
            session: 数据库会话
            local_project_id: 本地项目ID
            entity_type: 可选，过滤特定实体类型
            backend_type: 可选，过滤特定后端类型

        Returns:
            List[EntityMapping]: 映射列表
        """
        try:
            query = session.query(EntityMapping).filter(EntityMapping.local_project_id == local_project_id)

            # 添加可选过滤条件
            if entity_type:
                entity_type_enum = EntityType(entity_type)
                query = query.filter(EntityMapping.local_entity_type == entity_type_enum)

            if backend_type:
                backend_type_enum = BackendType(backend_type)
                query = query.filter(EntityMapping.backend_type == backend_type_enum)

            return query.all()

        except Exception as e:
            logger.error(f"获取项目映射时出错: {e}", exc_info=True)
            return []

    def get_or_create_mapping(
        self, session: Session, local_entity_id: str, local_entity_type: str, backend_type: str, **kwargs
    ) -> Tuple[EntityMapping, bool]:
        """
        获取或创建映射

        Args:
            session: 数据库会话
            local_entity_id: 本地实体ID
            local_entity_type: 本地实体类型
            backend_type: 后端类型
            **kwargs: 创建时的其他参数

        Returns:
            Tuple[EntityMapping, bool]: 映射对象和一个布尔值表示是否是新创建的
        """
        # 尝试获取现有映射
        mapping = self.get_mapping_by_local_id(session, local_entity_id, local_entity_type, backend_type)

        if mapping:
            return mapping, False

        # 创建新映射
        mapping = self.create_mapping(session, local_entity_id, local_entity_type, backend_type, **kwargs)

        return mapping, True
