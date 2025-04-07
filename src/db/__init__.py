"""
数据库服务包

提供数据库访问和实体管理功能
"""

import logging
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Updated imports for flow repositories
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.db.repositories.stage_instance_repository import StageInstanceRepository
from src.db.repositories.task_repository import TaskCommentRepository, TaskRepository
from src.db.repositories.template_repository import TemplateRepository, TemplateVariableRepository
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
from src.models.db import Base
from src.models.db.init_db import get_db_path, init_db

logger = logging.getLogger(__name__)


def get_engine(db_path=None):
    """获取数据库引擎

    优先级:
    1. 传入的 db_path 参数
    2. DATABASE_URL 环境变量
    3. 默认路径 (data/vibecopilot.db)

    Args:
        db_path: 显式指定的数据库文件路径

    Returns:
        SQLAlchemy引擎实例
    """
    if db_path:
        database_url = f"sqlite:///{db_path}"
    else:
        # 获取 DATABASE_URL 或使用默认路径
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            db_path = get_db_path()  # 使用 init_db.py 中的逻辑获取默认路径
            database_url = f"sqlite:///{db_path}"

    # 确保数据库目录存在
    if database_url.startswith("sqlite:///"):
        db_path = database_url[len("sqlite:///") :]
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    # logger.info(f"使用数据库URL: {database_url}")
    return create_engine(database_url, connect_args={"check_same_thread": False})


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


# 导出模块API
__all__ = [
    "init_db",
    "get_engine",
    "get_session_factory",
    "Base",
    "TemplateRepository",
    "TemplateVariableRepository",
    "FlowSessionRepository",
    "StageInstanceRepository",
    "WorkflowDefinitionRepository",
    "TaskRepository",
    "TaskCommentRepository",
]

# 注意: 不要在此处导入 service.py 或其他依赖 src.db 的模块，
# 避免循环导入。service.py 会直接导入所需的仓库类。
