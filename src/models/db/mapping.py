"""
实体映射数据库模型

用于存储本地实体与远程后端的映射关系，实现解耦的实体映射与本地编号。
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.models.db.base import Base


class EntityType(enum.Enum):
    """实体类型枚举"""

    ROADMAP = "roadmap"
    EPIC = "epic"
    STORY = "story"
    TASK = "task"
    MILESTONE = "milestone"


class BackendType(enum.Enum):
    """后端类型枚举"""

    GITHUB = "github"
    LINEAR = "linear"
    JIRA = "jira"
    ASANA = "asana"
    TRELLO = "trello"
    CUSTOM = "custom"


class EntityMapping(Base):
    """
    实体映射表

    存储本地实体与远程后端的映射关系，例如本地Epic与GitHub Issue的对应关系。
    这种解耦方式允许一个本地实体可以映射到多个不同的后端系统，且不需要修改核心实体数据结构。
    """

    __tablename__ = "entity_mappings"

    id = Column(String(36), primary_key=True)

    # 本地实体信息
    local_entity_id = Column(String(36), nullable=False, index=True)
    local_entity_type = Column(Enum(EntityType), nullable=False)

    # 本地项目上下文
    local_project_id = Column(String(36), nullable=True, index=True)

    # 远程后端类型与信息
    backend_type = Column(Enum(BackendType), nullable=False)
    remote_entity_id = Column(String(255), nullable=True, index=True)
    remote_entity_number = Column(String(50), nullable=True, index=True)

    # 远程项目上下文
    remote_project_id = Column(String(255), nullable=True, index=True)
    remote_project_context = Column(String(255), nullable=True)

    # 元数据
    last_synced_at = Column(DateTime, nullable=True)
    last_sync_direction = Column(String(20), nullable=True)  # "to_remote", "from_remote", "bidirectional"
    sync_data = Column(JSON, nullable=True)  # 存储同步相关的元数据

    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 索引和约束
    __table_args__ = (
        # 对(local_entity_id, local_entity_type, backend_type)建立唯一约束
        # 确保一个本地实体在同一后端类型只有一个映射
        UniqueConstraint("local_entity_id", "local_entity_type", "backend_type", name="uix_entity_backend"),
        # 对(remote_entity_id, backend_type)建立唯一约束
        # 确保一个远程实体只映射到一个本地实体
        UniqueConstraint("remote_entity_id", "backend_type", name="uix_remote_entity_backend"),
        # 联合索引，用于根据本地项目ID和实体类型查询映射
        Index("ix_project_entity_type", "local_project_id", "local_entity_type"),
        # 联合索引，用于根据后端类型和远程项目ID查询映射
        Index("ix_backend_remote_project", "backend_type", "remote_project_id"),
    )

    def __repr__(self):
        return (
            f"<EntityMapping(local={self.local_entity_type.value}:{self.local_entity_id}, "
            f"remote={self.backend_type.value}:{self.remote_entity_id or self.remote_entity_number})>"
        )
