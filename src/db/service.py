"""
数据库服务模块

提供统一的数据库服务接口，集成各Repository对象。
"""

import logging
from typing import Any, Dict, List, Optional

# 导入上层模块定义的数据库函数
from src.db import get_engine, get_session_factory
from src.db.core.entity_manager import EntityManager
from src.db.repositories.log_repository import (
    AuditLogRepository,
    ErrorLogRepository,
    OperationLogRepository,
    PerformanceLogRepository,
    TaskLogRepository,
    WorkflowLogRepository,
)
from src.db.repositories.roadmap_repository import EpicRepository, StoryRepository
from src.db.repositories.task_repository import TaskRepository
from src.db.specific_managers.epic_manager import EpicManager
from src.db.specific_managers.log_manager import LogManager
from src.db.specific_managers.story_manager import StoryManager
from src.db.specific_managers.task_manager import TaskManager

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
        # 单例模式，只初始化一次
        if self._initialized:
            logger.debug("DatabaseService已初始化，跳过重复初始化")
            return

        try:
            # 使用connection_manager确保数据库表已初始化
            from src.db.connection_manager import ensure_tables_exist, get_engine, get_session_factory

            # 确保表已初始化
            ensure_tables_exist()

            # 获取数据库引擎
            engine = get_engine()
            if not engine:
                logger.error("数据库引擎获取失败")
                raise RuntimeError("数据库引擎获取失败")

            # 使用会话工厂
            session_factory = get_session_factory()
            if not session_factory:
                logger.error("数据库会话工厂获取失败")
                raise RuntimeError("数据库会话工厂获取失败")

            self.session = session_factory()

            # 初始化各种仓库，所有实体类型都使用SQLAlchemy仓库
            from src.db.repositories.roadmap_repository import EpicRepository, StoryRepository
            from src.db.repositories.task_repository import TaskRepository

            self.epic_repo = EpicRepository(self.session)
            self.story_repo = StoryRepository(self.session)
            self.task_repo = TaskRepository(self.session)

            # 类型到仓库的映射
            self.repo_map = {
                "epic": self.epic_repo,
                "story": self.story_repo,
                "task": self.task_repo,
            }

            logger.debug(f"初始化的仓库: {', '.join(self.repo_map.keys())}")

            # 初始化实体管理器，不再传递模拟存储
            from src.db.core.entity_manager import EntityManager

            self.entity_manager = EntityManager(self.repo_map)

            # 验证实体管理器初始化正确
            if not hasattr(self.entity_manager, "repositories") or not self.entity_manager.repositories:
                logger.error("实体管理器初始化失败，repositories为空")
                raise RuntimeError("实体管理器初始化失败")

            # 初始化特定实体管理器，不再传递模拟存储
            from src.db.specific_managers.epic_manager import EpicManager
            from src.db.specific_managers.log_manager import LogManager
            from src.db.specific_managers.story_manager import StoryManager
            from src.db.specific_managers.task_manager import TaskManager

            self.epic_manager = EpicManager(self.entity_manager)
            self.story_manager = StoryManager(self.entity_manager)
            self.task_manager = TaskManager(self.entity_manager, self.task_repo)
            self.log_manager = LogManager(self.session)

            # 最后验证所有关键组件已初始化
            self._validate_initialization()

            # 标记已初始化
            self.__class__._initialized = True

            logger.info("数据库服务初始化成功")
        except Exception as e:
            logger.error(f"数据库服务初始化失败: {e}", exc_info=True)
            raise

    def _validate_initialization(self):
        """验证所有必要组件是否已正确初始化"""
        if not hasattr(self, "session") or self.session is None:
            raise RuntimeError("数据库会话未初始化")

        if not hasattr(self, "entity_manager") or self.entity_manager is None:
            raise RuntimeError("实体管理器未初始化")

        if not hasattr(self, "epic_manager") or self.epic_manager is None:
            raise RuntimeError("Epic管理器未初始化")

        if not hasattr(self, "story_manager") or self.story_manager is None:
            raise RuntimeError("Story管理器未初始化")

        if not hasattr(self, "task_manager") or self.task_manager is None:
            raise RuntimeError("Task管理器未初始化")

    # 通用实体管理方法，委托给实体管理器

    def get_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """通用获取实体方法

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            实体数据
        """
        return self.entity_manager.get_entity(entity_type, entity_id)

    def get_entities(self, entity_type: str) -> List[Dict[str, Any]]:
        """通用获取实体列表方法

        Args:
            entity_type: 实体类型

        Returns:
            实体列表
        """
        try:
            logger.info(f"尝试获取实体列表，类型: {entity_type}")

            # 检查会话
            if not hasattr(self, "session") or self.session is None:
                logger.error("数据库会话未初始化")
                raise RuntimeError("数据库会话未初始化")

            # 检查实体管理器
            if not hasattr(self, "entity_manager") or self.entity_manager is None:
                logger.error("实体管理器未初始化")
                raise RuntimeError("实体管理器未初始化")

            # 检查实体类型
            if entity_type not in self.repo_map:
                logger.warning(f"未知实体类型: {entity_type}，已知类型: {list(self.repo_map.keys())}")

            # 尝试使用特定方法
            if entity_type == "epic" and hasattr(self, "list_epics"):
                logger.info("使用list_epics方法获取epic列表")
                result = self.list_epics()
            elif entity_type == "story" and hasattr(self, "list_stories"):
                logger.info("使用list_stories方法获取story列表")
                result = self.list_stories()
            elif entity_type == "task" and hasattr(self, "list_tasks"):
                logger.info("使用list_tasks方法获取task列表")
                result = self.list_tasks()
            else:
                # 尝试获取实体列表
                logger.info(f"使用entity_manager.get_entities获取{entity_type}列表")
                result = self.entity_manager.get_entities(entity_type)

            logger.info(f"成功获取 {len(result)} 个 {entity_type} 实体")
            return result
        except Exception as e:
            logger.error(f"获取 {entity_type} 实体列表失败: {e}")
            raise

    def create_entity(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通用创建实体方法

        Args:
            entity_type: 实体类型
            data: 实体数据

        Returns:
            创建的实体
        """
        return self.entity_manager.create_entity(entity_type, data)

    def update_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """通用更新实体方法

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            data: 更新数据

        Returns:
            更新后的实体
        """
        return self.entity_manager.update_entity(entity_type, entity_id, data)

    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """通用删除实体方法

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            是否成功
        """
        return self.entity_manager.delete_entity(entity_type, entity_id)

    def search_entities(self, entity_type: str, query: str) -> List[Dict[str, Any]]:
        """通用搜索实体方法

        Args:
            entity_type: 实体类型
            query: 搜索关键词

        Returns:
            匹配的实体列表
        """
        return self.entity_manager.search_entities(entity_type, query)

    # Epic相关方法，委托给Epic管理器

    def get_epic(self, epic_id: str) -> Dict[str, Any]:
        """获取Epic信息"""
        return self.epic_manager.get_epic(epic_id)

    def list_epics(self) -> List[Dict[str, Any]]:
        """获取所有Epic"""
        return self.epic_manager.list_epics()

    def create_epic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Epic"""
        return self.epic_manager.create_epic(data)

    def update_epic(self, epic_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Epic"""
        return self.epic_manager.update_epic(epic_id, data)

    def delete_epic(self, epic_id: str) -> bool:
        """删除Epic"""
        return self.epic_manager.delete_epic(epic_id)

    # Story相关方法，委托给Story管理器

    def get_story(self, story_id: str) -> Dict[str, Any]:
        """获取Story信息"""
        return self.story_manager.get_story(story_id)

    def list_stories(self) -> List[Dict[str, Any]]:
        """获取所有Story"""
        return self.story_manager.list_stories()

    def create_story(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Story"""
        return self.story_manager.create_story(data)

    def update_story(self, story_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Story"""
        return self.story_manager.update_story(story_id, data)

    def delete_story(self, story_id: str) -> bool:
        """删除Story"""
        return self.story_manager.delete_story(story_id)

    # Task相关方法，委托给Task管理器

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """获取Task信息"""
        return self.task_manager.get_task(task_id)

    def list_tasks(self) -> List[Dict[str, Any]]:
        """获取所有Task"""
        return self.task_manager.list_tasks()

    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Task"""
        return self.task_manager.create_task(data)

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Task"""
        return self.task_manager.update_task(task_id, data)

    def delete_task(self, task_id: str) -> bool:
        """删除Task"""
        return self.task_manager.delete_task(task_id)

    # 其他特定实体类型方法

    def get_label(self, label_id: str) -> Dict[str, Any]:
        """获取Label信息"""
        return self.get_entity("label", label_id)

    def get_template(self, template_id: str) -> Dict[str, Any]:
        """获取Template信息"""
        return self.get_entity("template", template_id)

    def list_labels(self) -> List[Dict[str, Any]]:
        """获取所有Label"""
        return self.get_entities("label")

    def list_templates(self) -> List[Dict[str, Any]]:
        """获取所有Template"""
        return self.get_entities("template")

    def search_templates(self, query: str, tags=None) -> List[Dict[str, Any]]:
        """搜索模板"""
        return self.search_entities("template", query)

    def create_label(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Label"""
        return self.create_entity("label", data)

    def create_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建Template"""
        return self.create_entity("template", data)

    def update_label(self, label_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Label"""
        return self.update_entity("label", label_id, data)

    def update_template(self, template_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新Template"""
        return self.update_entity("template", template_id, data)

    def delete_label(self, label_id: str) -> bool:
        """删除Label"""
        return self.delete_entity("label", label_id)

    def delete_template(self, template_id: str) -> bool:
        """删除Template"""
        return self.delete_entity("template", template_id)

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
        """获取数据库统计信息"""
        # TODO: 实现统计逻辑
        return {"epic": 0, "story": 0, "task": 0, "label": 0, "template": 0}

    # 日志相关方法
    def get_log_manager(self) -> LogManager:
        """获取日志管理器"""
        return self.log_manager

    def get_workflow_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取工作流日志列表"""
        return self.log_manager.get_workflow_logs(limit, offset)

    def get_workflow_operations(self, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的操作日志"""
        return self.log_manager.get_workflow_operations(workflow_id)

    def get_operation_tasks(self, operation_id: str) -> List[Dict[str, Any]]:
        """获取指定操作的任务日志"""
        return self.log_manager.get_operation_tasks(operation_id)

    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的错误日志"""
        return self.log_manager.get_recent_errors(limit)

    def get_user_audit_logs(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取用户的审计日志"""
        return self.log_manager.get_user_audit_logs(user_id, limit)

    # 日志记录方法是通过log_service.py直接访问的，不需要在这里提供
