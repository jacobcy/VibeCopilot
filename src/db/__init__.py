"""
数据库服务包

提供数据库访问和实体管理功能
"""

import logging
import os
from typing import Optional

from sqlalchemy import Engine
from sqlalchemy.orm import Session

# 导入连接管理器
from src.db.connection_manager import connection_manager, ensure_tables_exist, get_engine, get_session, get_session_factory

# 创建默认会话工厂，提供与session.py同样的功能
SessionLocal = get_session_factory()


def get_db() -> Session:
    """获取数据库会话并确保会话关闭

    兼容session.py的get_db函数，确保会话正确关闭

    Returns:
        数据库会话对象
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


# Updated imports for flow repositories - 移动到需要它们的地方或由服务层管理
# from src.db.repositories.flow_session_repository import FlowSessionRepository
# from src.db.repositories.memory_item_repository import MemoryItemRepository
# from src.db.repositories.rule_repository import RuleExampleRepository, RuleItemRepository, RuleRepository
# from src.db.repositories.stage_instance_repository import StageInstanceRepository
# from src.db.repositories.task_repository import TaskCommentRepository, TaskRepository
# from src.db.repositories.template_repository import TemplateRepository, TemplateVariableRepository
# from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
from src.models.db.base import Base
from src.models.db.init_db import init_db

logger = logging.getLogger(__name__)


# 这些函数现在从连接管理器导入
# get_engine - 获取全局数据库引擎
# get_session - 获取新的数据库会话
# get_session_factory - 获取会话工厂
# ensure_tables_exist - 确保所有表存在


# 导出模块API
__all__ = [
    "init_db",
    "get_engine",
    "get_session",
    "get_session_factory",
    "ensure_tables_exist",
    "SessionLocal",
    "get_db",
    "Base",
]

# 注意: 不要在此处导入 service.py 或其他依赖 src.db 的模块，
# 避免循环导入。service.py 会直接导入所需的仓库类。


def init_database(force_recreate=False) -> bool:
    """初始化数据库并确保表已创建

    统一的初始化入口点，适用于CLI等需要确保数据库正确初始化的场景

    Args:
        force_recreate: 是否强制重新创建表

    Returns:
        bool: 初始化是否成功
    """
    logger.info("初始化数据库...")
    try:
        # 检查环境变量中的force_recreate设置
        env_force = os.getenv("FORCE_RECREATE", "").lower() == "true"
        force_recreate = force_recreate or env_force

        # 确保表已创建
        ensure_tables_exist(force_recreate=force_recreate)

        # 验证数据库引擎可用
        engine = get_engine()
        if not engine:
            logger.error("数据库引擎初始化失败")
            return False

        # 初始化数据
        from src.db.init_data import init_all_data

        init_all_data()

        logger.info("数据库初始化成功")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}", exc_info=True)
        return False
