"""
数据库服务模块

提供统一的数据库服务接口，集成各Repository对象。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

# 导入上层模块定义的数据库函数
from src.db import get_engine, get_session_factory
from src.db.core.entity_manager import EntityManager
from src.db.core.epic_manager import EpicManager
from src.db.core.log_manager import LogManager
from src.db.core.story_manager import StoryManager
from src.db.core.task_manager import TaskManager
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.db.repositories.log_repository import (
    AuditLogRepository,
    ErrorLogRepository,
    OperationLogRepository,
    PerformanceLogRepository,
    TaskLogRepository,
    WorkflowLogRepository,
)
from src.db.repositories.memory_item_repository import MemoryItemRepository
from src.db.repositories.roadmap_repository import EpicRepository, StoryRepository
from src.db.repositories.rule_repository import RuleRepository
from src.db.repositories.stage_instance_repository import StageInstanceRepository
from src.db.repositories.stage_repository import StageRepository
from src.db.repositories.task_repository import TaskRepository
from src.db.repositories.template_repository import TemplateRepository
from src.db.repositories.transition_repository import TransitionRepository
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository

# 直接从各自的模块导入
from src.models.db.init_db import init_db

logger = logging.getLogger(__name__)


class DatabaseService:
    """数据库服务类，整合各Repository提供统一接口"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式实现，确保全局只有一个实例"""
        if cls._instance is None:
            logger.debug("创建DatabaseService单例实例")
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化数据库服务"""
        if self._initialized:
            logger.debug("DatabaseService已初始化，跳过重复初始化")
            return

        try:
            from src.db.connection_manager import ensure_tables_exist, get_engine, get_session_factory

            ensure_tables_exist()
            engine = get_engine()
            if not engine:
                logger.error("数据库引擎获取失败")
                raise RuntimeError("数据库引擎获取失败")

            # 初始化各种仓库，不再传递 session
            from src.db.repositories.flow_session_repository import FlowSessionRepository
            from src.db.repositories.memory_item_repository import MemoryItemRepository
            from src.db.repositories.roadmap_repository import EpicRepository, StoryRepository
            from src.db.repositories.rule_repository import RuleRepository
            from src.db.repositories.stage_instance_repository import StageInstanceRepository
            from src.db.repositories.stage_repository import StageRepository
            from src.db.repositories.task_repository import TaskRepository
            from src.db.repositories.template_repository import TemplateRepository
            from src.db.repositories.transition_repository import TransitionRepository
            from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository

            # Import log repositories if they need to be in repo_map (currently not planned)
            # from src.db.repositories.log_repository import ...

            self.epic_repo = EpicRepository()
            self.story_repo = StoryRepository()
            self.task_repo = TaskRepository()
            self.memory_item_repo = MemoryItemRepository()
            self.rule_repo = RuleRepository()
            self.template_repo = TemplateRepository()
            self.workflow_repo = WorkflowDefinitionRepository()
            self.stage_repo = StageRepository()
            self.flow_session_repo = FlowSessionRepository()
            self.stage_instance_repo = StageInstanceRepository()
            self.transition_repo = TransitionRepository()

            self.repo_map = {
                "epic": self.epic_repo,
                "story": self.story_repo,
                "task": self.task_repo,
                "memory_item": self.memory_item_repo,
                "rule": self.rule_repo,
                "template": self.template_repo,
                "workflow": self.workflow_repo,  # Maps to WorkflowDefinitionRepository
                "stage": self.stage_repo,
                "flow_session": self.flow_session_repo,
                "stage_instance": self.stage_instance_repo,
                "transition": self.transition_repo,
                # Add other repositories here if needed for EntityManager
            }

            logger.debug(f"初始化的仓库 (in repo_map): {', '.join(self.repo_map.keys())}")

            # 初始化实体管理器，不再传递 session
            from src.db.core.entity_manager import EntityManager

            self.entity_manager = EntityManager(self.repo_map)

            # 验证实体管理器初始化
            if not hasattr(self.entity_manager, "repositories") or not self.entity_manager.repositories:
                logger.error("实体管理器初始化失败，repositories为空")
                raise RuntimeError("实体管理器初始化失败")

            # 初始化特定实体管理器，不再传递 session
            from src.db.core.epic_manager import EpicManager
            from src.db.core.log_manager import LogManager
            from src.db.core.story_manager import StoryManager
            from src.db.core.task_manager import TaskManager

            self.epic_manager = EpicManager(self.entity_manager)
            self.story_manager = StoryManager(self.entity_manager)
            self.task_manager = TaskManager(self.entity_manager, self.task_repo)
            self.log_manager = LogManager()

            self._validate_initialization()
            self.__class__._initialized = True
            logger.info("数据库服务初始化成功")
        except Exception as e:
            logger.error(f"数据库服务初始化失败: {e}", exc_info=True)
            raise

    def _validate_initialization(self):
        """验证所有必要组件是否已正确初始化"""
        if not hasattr(self, "entity_manager") or self.entity_manager is None:
            raise RuntimeError("实体管理器未初始化")

        if not hasattr(self, "epic_manager") or self.epic_manager is None:
            raise RuntimeError("Epic管理器未初始化")

        if not hasattr(self, "story_manager") or self.story_manager is None:
            raise RuntimeError("Story管理器未初始化")

        if not hasattr(self, "task_manager") or self.task_manager is None:
            raise RuntimeError("Task管理器未初始化")

        if not hasattr(self, "memory_item_repo") or self.memory_item_repo is None:
            raise RuntimeError("MemoryItemRepository未初始化")

    # 通用实体管理方法，委托给实体管理器

    def get_entity(self, session: Session, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """通用获取实体方法

        Args:
            session: 数据库会话
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            实体数据
        """
        return self.entity_manager.get_entity(session, entity_type, entity_id)

    def get_entities(self, session: Session, entity_type: str) -> List[Dict[str, Any]]:
        """通用获取实体列表方法

        Args:
            session: 数据库会话
            entity_type: 实体类型

        Returns:
            实体列表
        """
        try:
            logger.info(f"尝试获取实体列表，类型: {entity_type}")

            if not hasattr(self, "entity_manager") or self.entity_manager is None:
                logger.error("实体管理器未初始化")
                raise RuntimeError("实体管理器未初始化")

            if entity_type not in self.repo_map:
                logger.warning(f"未知实体类型: {entity_type}，已知类型: {list(self.repo_map.keys())}")
                return []

            # 尝试使用特定方法
            if entity_type == "epic" and hasattr(self, "list_epics"):
                logger.info("使用list_epics方法获取epic列表")
                result = self.list_epics(session)
            elif entity_type == "story" and hasattr(self, "list_stories"):
                logger.info("使用list_stories方法获取story列表")
                result = self.list_stories(session)
            elif entity_type == "task" and hasattr(self, "list_tasks"):
                logger.info("使用list_tasks方法获取task列表")
                result = self.list_tasks(session)
            else:
                # 尝试获取实体列表
                logger.info(f"使用entity_manager.get_entities获取{entity_type}列表")
                result = self.entity_manager.get_entities(session, entity_type)

            logger.info(f"成功获取 {len(result)} 个 {entity_type} 实体")
            return result
        except Exception as e:
            logger.error(f"获取 {entity_type} 实体列表失败: {e}")
            raise

    def create_entity(self, session: Session, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通用创建实体方法

        Args:
            session: 数据库会话
            entity_type: 实体类型
            data: 实体数据

        Returns:
            创建的实体
        """
        return self.entity_manager.create_entity(session, entity_type, data)

    def update_entity(self, session: Session, entity_type: str, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通用更新实体方法

        Args:
            session: 数据库会话
            entity_type: 实体类型
            entity_id: 实体ID
            data: 更新数据

        Returns:
            更新后的实体
        """
        return self.entity_manager.update_entity(session, entity_type, entity_id, data)

    def delete_entity(self, session: Session, entity_type: str, entity_id: str) -> bool:
        """通用删除实体方法

        Args:
            session: 数据库会话
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            是否成功
        """
        return self.entity_manager.delete_entity(session, entity_type, entity_id)

    def search_entities(self, session: Session, entity_type: str, query: str) -> List[Dict[str, Any]]:
        """通用搜索实体方法

        Args:
            session: 数据库会话
            entity_type: 实体类型
            query: 搜索关键词

        Returns:
            匹配的实体列表
        """
        return self.entity_manager.search_entities(session, entity_type, query)

    # Epic相关方法，委托给Epic管理器

    def get_epic(self, session: Session, epic_id: str) -> Dict[str, Any]:
        """获取Epic信息"""
        epic = self.epic_repo.get_by_id(session, epic_id)
        return epic.to_dict() if epic else None

    def list_epics(self, session: Session) -> List[Dict[str, Any]]:
        """获取所有Epic"""
        epics = self.epic_repo.get_all(session)
        return [epic.to_dict() for epic in epics]

    def create_epic(self, session: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Epic"""
        epic = self.epic_repo.create(session, **data)
        return epic.to_dict()

    def update_epic(self, session: Session, epic_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Epic"""
        epic = self.epic_repo.update(session, epic_id, data)
        return epic.to_dict() if epic else None

    def delete_epic(self, session: Session, epic_id: str) -> bool:
        """删除Epic"""
        return self.epic_repo.delete(session, epic_id)

    # Story相关方法，委托给Story管理器

    def get_story(self, session: Session, story_id: str) -> Dict[str, Any]:
        """获取Story信息"""
        story = self.story_repo.get_by_id(session, story_id)
        return story.to_dict() if story else None

    def list_stories(self, session: Session) -> List[Dict[str, Any]]:
        """获取所有Story"""
        stories = self.story_repo.get_all(session)
        return [story.to_dict() for story in stories]

    def create_story(self, session: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Story"""
        story = self.story_repo.create(session, **data)
        return story.to_dict()

    def update_story(self, session: Session, story_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Story"""
        story = self.story_repo.update(session, story_id, data)
        return story.to_dict() if story else None

    def delete_story(self, session: Session, story_id: str) -> bool:
        """删除Story"""
        return self.story_repo.delete(session, story_id)

    # Task相关方法，委托给Task管理器

    def get_task(self, session: Session, task_id: str) -> Dict[str, Any]:
        """获取Task信息"""
        task = self.task_repo.get_by_id(session, task_id)
        return task.to_dict() if task else None

    def list_tasks(self, session: Session) -> List[Dict[str, Any]]:
        """获取所有Task"""
        tasks = self.task_repo.get_all(session)
        return [task.to_dict() for task in tasks]

    def create_task(self, session: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Task"""
        task = self.task_repo.create_task(session, **data)
        return task.to_dict()

    def update_task(self, session: Session, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Task"""
        task = self.task_repo.update_task(session, task_id, data)
        return task.to_dict() if task else None

    def delete_task(self, session: Session, task_id: str) -> bool:
        """删除Task"""
        return self.task_repo.delete(session, task_id)

    # 其他特定实体类型方法

    def get_label(self, session: Session, label_id: str) -> Dict[str, Any]:
        """获取Label信息"""
        logger.warning("get_label 方法未完全实现 session 传递")
        return None

    def get_template(self, session: Session, template_id: str) -> Dict[str, Any]:
        """获取Template信息"""
        logger.warning("get_template 方法未完全实现 session 传递")
        return None

    def list_labels(self, session: Session) -> List[Dict[str, Any]]:
        """获取所有Label"""
        logger.warning("list_labels 方法未完全实现 session 传递")
        return []

    def list_templates(self, session: Session) -> List[Dict[str, Any]]:
        """获取所有Template"""
        logger.warning("list_templates 方法未完全实现 session 传递")
        return []

    def search_templates(self, session: Session, query: str, tags=None) -> List[Dict[str, Any]]:
        """搜索模板"""
        logger.warning("search_templates 方法未完全实现 session 传递")
        return []

    def create_label(self, session: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Label"""
        logger.warning("create_label 方法未完全实现 session 传递")
        return {}

    def create_template(self, session: Session, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Template"""
        logger.warning("create_template 方法未完全实现 session 传递")
        return {}

    def update_label(self, session: Session, label_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Label"""
        logger.warning("update_label 方法未完全实现 session 传递")
        return None

    def update_template(self, session: Session, template_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Template"""
        logger.warning("update_template 方法未完全实现 session 传递")
        return None

    def delete_label(self, session: Session, label_id: str) -> bool:
        """删除Label"""
        logger.warning("delete_label 方法未完全实现 session 传递")
        return False

    def delete_template(self, session: Session, template_id: str) -> bool:
        """删除Template"""
        logger.warning("delete_template 方法未完全实现 session 传递")
        return False

    def backup(self, path: Optional[str] = None) -> str:
        """备份数据库"""
        # TODO: 实现备份逻辑
        return path or "backup.db"

    def restore(self, path: str) -> None:
        """从备份文件恢复数据库"""
        # TODO: 实现恢复逻辑
        pass

    def clean(self) -> None:
        """
        清理数据库中的历史数据

        目前主要清理日志数据，防止日志过多导致数据库膨胀
        """
        try:
            # 获取各类日志仓库
            workflow_log_repo = WorkflowLogRepository(self.session)
            operation_log_repo = OperationLogRepository(self.session)
            task_log_repo = TaskLogRepository(self.session)
            error_log_repo = ErrorLogRepository(self.session)
            performance_log_repo = PerformanceLogRepository(self.session)
            audit_log_repo = AuditLogRepository(self.session)

            # 获取所有日志实体表
            logs_to_clean = [
                workflow_log_repo.model,
                operation_log_repo.model,
                task_log_repo.model,
                error_log_repo.model,
                performance_log_repo.model,
                audit_log_repo.model,
            ]

            # 清理所有日志表
            for log_entity in logs_to_clean:
                count = self.session.query(log_entity).delete()
                logger.info(f"已清理 {count} 条 {log_entity.__tablename__} 数据")

            self.session.commit()
            logger.info("日志数据清理完成")
        except Exception as e:
            self.session.rollback()
            logger.error(f"清理日志数据失败: {e}", exc_info=True)
            raise

    def get_stats(self) -> Dict[str, int]:
        """获取数据库统计信息

        Returns:
            Dict[str, int]: 包含各实体类型记录数的字典
        """
        try:
            result = {}

            # 获取Epic表统计
            from src.models.db import Epic

            epic_count = self.session.query(Epic).count()
            result["epic"] = epic_count

            # 获取Story表统计
            from src.models.db import Story

            story_count = self.session.query(Story).count()
            result["story"] = story_count

            # 获取Task表统计
            from src.models.db.task import Task

            task_count = self.session.query(Task).count()
            result["task"] = task_count

            # 获取MemoryItem表统计
            from src.models.db import MemoryItem

            if hasattr(self.session, "query") and MemoryItem is not None:
                memory_item_count = self.session.query(MemoryItem).filter(MemoryItem.is_deleted == False).count()
                result["memory_item"] = memory_item_count
            else:
                result["memory_item"] = 0

            # 获取Label表统计
            from src.models.db import Label

            if hasattr(self.session, "query") and Label is not None:
                label_count = self.session.query(Label).count()
                result["label"] = label_count
            else:
                result["label"] = 0

            # 获取Template表统计
            from src.models.db import Template

            if hasattr(self.session, "query") and Template is not None:
                template_count = self.session.query(Template).count()
                result["template"] = template_count
            else:
                result["template"] = 0

            logger.info(f"获取数据库统计信息成功: {result}")
            return result
        except Exception as e:
            logger.error(f"获取数据库统计信息失败: {str(e)}", exc_info=True)
            # 返回默认值，避免前端报错
            return {"epic": 0, "story": 0, "task": 0, "label": 0, "template": 0, "memory_item": 0}

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """获取数据库表结构信息

        Args:
            table_name: 表名称，如 'task', 'epic', 'story' 等

        Returns:
            Dict[str, Any]: 包含表结构信息的字典
        """
        try:
            # 获取对应的模型类
            model_map = {"epic": "Epic", "story": "Story", "task": "Task", "label": "Label", "template": "Template", "memory_item": "MemoryItem"}

            if table_name.lower() not in model_map:
                return {"error": f"不支持的表名: {table_name}"}

            # 导入对应的模型
            if table_name.lower() == "task":
                from src.models.db.task import Task as Model
            else:
                from src.models.db import Epic, Label, MemoryItem, Story, Template

                model_class_name = model_map[table_name.lower()]
                Model = locals()[model_class_name]

            # 获取表信息
            from sqlalchemy import inspect

            inspector = inspect(self.session.bind)
            columns = inspector.get_columns(Model.__tablename__)

            # 查询表记录数量
            count = self.session.query(Model).count()

            # 获取几条示例数据
            examples = []
            sample_rows = self.session.query(Model).limit(3).all()
            for row in sample_rows:
                examples.append({c.name: getattr(row, c.name) for c in row.__table__.columns})

            return {
                "table_name": Model.__tablename__,
                "count": count,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "default": str(col["default"]) if col["default"] is not None else None,
                    }
                    for col in columns
                ],
                "examples": examples,
            }
        except Exception as e:
            logger.error(f"获取表结构信息失败: {str(e)}", exc_info=True)
            return {"error": str(e)}

    # 日志相关方法
    def get_log_manager(self) -> LogManager:
        """获取日志管理器"""
        return self.log_manager

    def get_workflow_logs(self, session: Session, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取工作流日志列表"""
        return self.log_manager.get_workflow_logs(session, limit, offset)

    def get_workflow_operations(self, session: Session, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的操作日志"""
        return self.log_manager.get_workflow_operations(session, workflow_id)

    def get_operation_tasks(self, session: Session, operation_id: str) -> List[Dict[str, Any]]:
        """获取指定操作的任务日志"""
        return self.log_manager.get_operation_tasks(session, operation_id)

    def get_recent_errors(self, session: Session, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的错误日志"""
        return self.log_manager.get_recent_errors(session, limit)

    def get_user_audit_logs(self, session: Session, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取用户的审计日志"""
        return self.log_manager.get_user_audit_logs(session, user_id, limit)

    # 日志记录方法是通过log_service.py直接访问的，不需要在这里提供
