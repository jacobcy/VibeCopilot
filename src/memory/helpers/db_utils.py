#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库工具模块

提供数据库初始化、会话管理等功能，简化记忆服务的数据库操作。
"""

import logging
import os
from typing import Optional, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import get_config

from .path_helpers import ensure_dir_exists, resolve_path

logger = logging.getLogger(__name__)


def init_db_engine(db_path: Optional[str] = None) -> Tuple[object, str]:
    """初始化数据库引擎

    Args:
        db_path: 数据库路径，默认使用配置中的路径

    Returns:
        Tuple[Engine, str]: SQLAlchemy引擎对象和规范化后的数据库路径
    """
    if db_path is None:
        db_path = get_config().get("database.url")

    # 确保路径规范化并处理用户路径（如~）
    db_path = resolve_path(db_path)

    # 确保数据库目录存在
    db_dir = os.path.dirname(db_path)
    ensure_dir_exists(db_dir)

    logger.info(f"初始化数据库引擎，数据库路径: {db_path}")
    return create_engine(f"sqlite:///{db_path}"), db_path


def create_tables(engine) -> None:
    """创建所有表

    Args:
        engine: SQLAlchemy引擎对象
    """
    # 延迟导入避免循环依赖
    from src.models.db.base import Base

    # 导入所有模型确保它们被注册到Base元类
    from src.models.db.memory_item import MemoryItem, SyncStatus

    Base.metadata.create_all(engine)
    logger.info("创建数据库表完成")


def get_session(engine) -> Session:
    """获取数据库会话

    Args:
        engine: SQLAlchemy引擎对象

    Returns:
        Session: SQLAlchemy会话对象
    """
    Session = sessionmaker(bind=engine)
    return Session()
