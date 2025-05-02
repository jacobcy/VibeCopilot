"""
数据库服务包

提供数据库访问和实体管理功能
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

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
    "DatabaseService",
]

# 注意: 不要在此处导入 service.py 或其他依赖 src.db 的模块，
# 避免循环导入。service.py 会直接导入所需的仓库类。


def init_database(force_recreate=False) -> Tuple[bool, Dict[str, Dict[str, int]]]:
    """初始化数据库并确保表已创建，返回初始化结果和统计信息

    统一的初始化入口点，适用于CLI等需要确保数据库正确初始化的场景

    Args:
        force_recreate: 是否强制重新创建表

    Returns:
        Tuple[bool, Dict[str, Dict[str, int]]]: (初始化是否成功, 初始化统计信息)
    """
    logger.info("初始化数据库...")
    init_stats = {}
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
            return False, init_stats

        # 初始化数据
        from src.db.init_data import init_all_data

        init_stats = init_all_data()

        logger.info("数据库初始化成功")
        return True, init_stats
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}", exc_info=True)
        return False, init_stats


# 数据库服务类
class DatabaseService:
    """数据库服务，提供统一的数据库操作接口"""

    def __init__(self, **kwargs):
        """初始化数据库服务"""
        self.logger = logging.getLogger(__name__)
        self.engine = get_engine()
        if not self.engine:
            self.logger.error("无法初始化数据库引擎")
            raise RuntimeError("数据库引擎初始化失败")
        self.verbose = kwargs.get("verbose", False)

        # 初始化仓库映射
        from src.db.repositories.roadmap_repository import EpicRepository, MilestoneRepository, RoadmapRepository, StoryRepository, TaskRepository

        self.repo_map = {
            "epic": EpicRepository(),
            "story": StoryRepository(),
            "task": TaskRepository(),
            "milestone": MilestoneRepository(),
            "roadmap": RoadmapRepository(),
        }

        if self.verbose:
            self.logger.debug("创建数据库服务，详细模式")
            self.logger.debug(f"初始化仓库映射: {list(self.repo_map.keys())}")

    def get_session(self) -> Session:
        """获取新的数据库会话"""
        return get_session()

    def get_entities(self, session: Session, entity_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的实体列表

        Args:
            session: 数据库会话
            entity_type: 实体类型

        Returns:
            List[Dict[str, Any]]: 实体列表
        """
        try:
            if self.verbose:
                self.logger.debug(f"获取 {entity_type} 实体列表")

            # 使用仓库映射获取实体
            if entity_type in self.repo_map:
                repository = self.repo_map[entity_type]
                entities = repository.get_all(session)
            else:
                raise ValueError(f"未知实体类型: {entity_type}")

            # 转换为字典列表
            result = []
            for entity in entities:
                if hasattr(entity, "to_dict"):
                    result.append(entity.to_dict())
                else:
                    result.append(entity.__dict__)

            return result
        except Exception as e:
            self.logger.error(f"获取实体列表时出错: {e}")
            return []

    def get_entities_simplified(self, session: Session, entity_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的实体列表，但不递归包含关联实体

        Args:
            session: 数据库会话
            entity_type: 实体类型

        Returns:
            List[Dict[str, Any]]: 简化的实体列表
        """
        try:
            if self.verbose:
                self.logger.debug(f"获取简化的 {entity_type} 实体列表")

            # 使用仓库映射获取实体
            if entity_type in self.repo_map:
                repository = self.repo_map[entity_type]
                entities = repository.get_all(session)
            else:
                raise ValueError(f"未知实体类型: {entity_type}")

            # 转换为简化的字典列表
            result = []
            for entity in entities:
                # 使用基础的 to_dict 方法，不递归包含关联实体
                if hasattr(entity, "__table__"):
                    entity_dict = {}
                    for column in entity.__table__.columns:
                        entity_dict[column.name] = getattr(entity, column.name)

                    # 对于 roadmap 类型，添加 epics_count 和 milestones_count
                    if entity_type == "roadmap" and hasattr(entity, "epics") and hasattr(entity, "milestones"):
                        entity_dict["epics_count"] = len(entity.epics) if entity.epics else 0
                        entity_dict["milestones_count"] = len(entity.milestones) if entity.milestones else 0

                        # 处理 tags 字段
                        if "tags" in entity_dict and entity_dict["tags"]:
                            import json

                            try:
                                entity_dict["tags"] = json.loads(entity_dict["tags"])
                            except:
                                entity_dict["tags"] = []

                    result.append(entity_dict)
                else:
                    # 如果不是 SQLAlchemy 模型，使用 __dict__
                    result.append(entity.__dict__)

            return result
        except Exception as e:
            self.logger.error(f"获取简化实体列表时出错: {e}")
            return []

    def get_entity(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """获取指定ID的实体"""
        session = self.get_session()
        try:
            if entity_type == "epic":
                from src.models.db.epic import Epic

                entity = session.query(Epic).filter(Epic.id == entity_id).first()
            elif entity_type == "story":
                from src.models.db.story import Story

                entity = session.query(Story).filter(Story.id == entity_id).first()
            elif entity_type == "task":
                from src.models.db.task import Task

                entity = session.query(Task).filter(Task.id == entity_id).first()
            else:
                raise ValueError(f"未知实体类型: {entity_type}")

            if entity:
                if hasattr(entity, "to_dict"):
                    return entity.to_dict()
                else:
                    return entity.__dict__
            return None
        finally:
            session.close()
