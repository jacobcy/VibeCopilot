"""
数据库模块

提供VibeCopilot统一数据库访问层，包括：
1. 数据库连接管理
2. 数据访问对象(Repository)
3. 事务处理
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.db import Base  # 直接从模型模块导入Base

# 默认数据库配置
DEFAULT_DB_PATH = os.path.join(Path.home(), ".vibecopilot", "database.sqlite")


def get_engine(db_path=None):
    """获取数据库引擎

    Args:
        db_path: 数据库文件路径，如果不指定则使用默认路径

    Returns:
        SQLAlchemy引擎实例
    """
    if not db_path:
        from src.core.config import get_config

        config = get_config()
        db_path = config.get("database.path", DEFAULT_DB_PATH)

    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # 创建引擎
    db_url = f"sqlite:///{db_path}"
    return create_engine(db_url, connect_args={"check_same_thread": False})


def get_session_factory(engine=None):
    """获取会话工厂

    Args:
        engine: SQLAlchemy引擎实例，如果不指定则创建新实例

    Returns:
        会话工厂函数
    """
    if not engine:
        engine = get_engine()

    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(engine=None, create_tables=True):
    """初始化数据库

    Args:
        engine: SQLAlchemy引擎实例，如果不指定则创建新实例
        create_tables: 是否创建表结构

    Returns:
        SQLAlchemy引擎实例
    """
    if not engine:
        engine = get_engine()

    if create_tables:
        # 创建表结构
        Base.metadata.create_all(bind=engine)

    return engine


from .repositories import (
    BlockRepository,
    DocumentRepository,
    EpicRepository,
    LinkRepository,
    MilestoneRepository,
    RoadmapRepository,
    StoryRepository,
    TaskRepository,
    TemplateRepository,
    TemplateVariableRepository,
    WorkflowRepository,
    WorkflowStepRepository,
)

# 导出API
from .repository import Repository

__all__ = [
    "get_engine",
    "get_session_factory",
    "init_db",
    "Base",
    "Repository",
    "EpicRepository",
    "MilestoneRepository",
    "RoadmapRepository",
    "StoryRepository",
    "TaskRepository",
    "DocumentRepository",
    "BlockRepository",
    "LinkRepository",
    "TemplateRepository",
    "TemplateVariableRepository",
    "WorkflowRepository",
    "WorkflowStepRepository",
]
