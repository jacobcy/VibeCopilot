"""
数据库服务包

提供数据库访问和实体管理功能
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.repositories.flow_session_repository import (
    FlowSessionRepository,
    StageInstanceRepository,
    WorkflowDefinitionRepository,
)
from src.db.repositories.template_repository import TemplateRepository, TemplateVariableRepository
from src.models.db import Base  # 直接从模型模块导入Base
from src.models.db.init_db import get_db_path, init_db  # 导入数据库初始化相关函数


# 从本模块定义基础数据库函数
def get_engine(db_path=None):
    """获取数据库引擎

    Args:
        db_path: 数据库文件路径，如果不指定则使用默认路径

    Returns:
        SQLAlchemy引擎实例
    """
    if not db_path:
        # 使用统一的获取数据库路径函数
        db_path = get_db_path()

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


# 导出模块API - 不导入其他模块，避免循环导入
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
]

# 注意: 不要在此处导入 service.py 或其他依赖 src.db 的模块，
# 避免循环导入。service.py 会直接导入所需的仓库类。
