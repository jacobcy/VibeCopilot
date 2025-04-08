"""
数据库服务包

提供数据库访问和实体管理功能
"""

import logging

from sqlalchemy import Engine
from sqlalchemy.orm import Session

# 导入连接管理器
from src.db.connection_manager import ensure_tables_exist, get_engine, get_session, get_session_factory

# Updated imports for flow repositories
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.db.repositories.rule_repository import RuleExampleRepository, RuleItemRepository, RuleRepository
from src.db.repositories.stage_instance_repository import StageInstanceRepository
from src.db.repositories.task_repository import TaskCommentRepository, TaskRepository
from src.db.repositories.template_repository import TemplateRepository, TemplateVariableRepository
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
from src.models.db import Base
from src.models.db.init_db import get_db_path, init_db

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
    "Base",
    "TemplateRepository",
    "TemplateVariableRepository",
    "RuleRepository",
    "RuleItemRepository",
    "RuleExampleRepository",
    "FlowSessionRepository",
    "StageInstanceRepository",
    "WorkflowDefinitionRepository",
    "TaskRepository",
    "TaskCommentRepository",
]

# 注意: 不要在此处导入 service.py 或其他依赖 src.db 的模块，
# 避免循环导入。service.py 会直接导入所需的仓库类。
