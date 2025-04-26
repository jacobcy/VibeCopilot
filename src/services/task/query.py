"""
任务查询服务模块

提供任务的查询、过滤等功能。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repositories.task_repository import TaskRepository
from src.db.session_manager import session_scope

logger = logging.getLogger(__name__)


class TaskQueryService:
    """任务查询服务类，负责任务的查询和过滤操作"""

    def __init__(self):
        """初始化任务查询服务"""
        # 直接实例化 Repository
        self._task_repo = TaskRepository()
        # 获取状态服务实例
        from src.status.service import StatusService

        self._status_service = StatusService.get_instance()

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """获取当前任务

        现在使用 Provider 模式获取当前任务 ID。
        """
        try:
            # 使用 Provider 获取当前任务 ID
            task_provider = self._status_service.provider_manager.get_provider("task")
            current_task_id = None

            if task_provider and hasattr(task_provider, "get_current_task_id"):
                current_task_id = task_provider.get_current_task_id()

            # 如果获取到 ID，则从数据库获取任务详情
            if current_task_id:
                # 使用 session_scope 获取会话
                with session_scope() as session:
                    # 使用 self._task_repo
                    task = self._task_repo.get_by_id(session, current_task_id)
                    return task.to_dict() if task else None
            else:
                return None
        except Exception as e:
            logger.error(f"获取当前任务失败: {e}")
            return None

    def get_task(self, session: Session, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情

        Args:
            session: 数据库会话
            task_id: 任务ID

        Returns:
            任务信息字典，如果找不到则返回None
        """
        try:
            # 使用 self._task_repo 获取任务
            task = self._task_repo.get_by_id(session, task_id)
            return task.to_dict() if task else None
        except Exception as e:
            logger.error(f"获取任务 {task_id} 失败: {e}")
            return None

    def get_task_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """通过ID或名称查找任务

        先按ID精确查找，如果找不到，则按名称（不区分大小写）查找。

        Args:
            identifier: 任务ID或任务名称

        Returns:
            任务信息字典，如果找不到则返回None
        """
        try:
            # 使用 session_scope 获取会话
            with session_scope() as session:
                # 首先尝试通过ID查找
                task_orm = self._task_repo.get_by_id(session, identifier)
                if task_orm:
                    return task_orm.to_dict() if hasattr(task_orm, "to_dict") else None

                # 如果找不到，尝试通过名称查找（不区分大小写）
                tasks_orm = self._task_repo.get_all(session)  # 获取所有 ORM 对象
                logger.debug(f"[get_task_by_identifier] Found {len(tasks_orm)} tasks via get_all for title comparison.")  # <-- 日志1
                found_task_dict = None
                for task_orm_item in tasks_orm:
                    task_title = getattr(task_orm_item, "title", "")
                    task_id = getattr(task_orm_item, "id", "N/A")
                    logger.debug(
                        f"[get_task_by_identifier] Comparing identifier '{identifier.lower()}' with task title '{task_title.lower()}' (ID: {task_id})"
                    )  # <-- 日志2
                    if task_title.lower() == identifier.lower():
                        logger.debug(f"[get_task_by_identifier] Title match found for identifier '{identifier}'! Task ID: {task_id}")  # <-- 日志3
                        # 转换为字典
                        found_task_dict = task_orm_item.to_dict() if hasattr(task_orm_item, "to_dict") else None
                        break  # 找到就退出循环

                if found_task_dict:
                    return found_task_dict
                # 都找不到，返回None
                logger.debug(f"[get_task_by_identifier] No title match found for identifier '{identifier}'.")  # <-- 日志4
                return None

        except Exception as e:
            logger.error(f"通过标识符 {identifier} 查找任务失败: {e}", exc_info=True)  # 添加 exc_info
            return None

    def list_tasks(
        self,
        session: Session,
        status: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        story_id: Optional[str] = None,
        is_independent: Optional[bool] = None,
        is_temporary: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """获取任务列表，支持多种过滤条件

        Args:
            session: 数据库会话
            status: 按状态过滤
            assignee: 按负责人过滤
            labels: 按标签过滤
            story_id: 按关联的Story ID过滤
            is_independent: 是否只返回独立任务 (映射到 is_temporary=True)
            is_temporary: 是否为临时任务
            limit: 返回结果数量限制
            offset: 结果偏移量

        Returns:
            任务列表
        """
        try:
            # 使用 self._task_repo.search_tasks
            tasks = self._task_repo.search_tasks(
                session,
                status=status,
                assignee=assignee,
                labels=labels,
                story_id=story_id,
                is_independent=is_independent,
                is_temporary=is_temporary,
                limit=limit,
                offset=offset,
            )
            return [task.to_dict() if hasattr(task, "to_dict") else task for task in tasks]

        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []

    def search_tasks(
        self,
        session: Session,
        status: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        story_id: Optional[str] = None,
        is_independent: Optional[bool] = None,
        is_temporary: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """搜索和过滤任务

        与list_tasks类似，但支持更多过滤条件和参数名称与TaskService一致

        Args:
            session: 数据库会话
            status: 状态列表
            assignee: 负责人
            labels: 标签列表
            story_id: 关联的故事ID
            is_independent: 是否为独立任务 (映射到 is_temporary=True)
            is_temporary: 是否为临时任务
            limit: 限制数量
            offset: 偏移量

        Returns:
            符合条件的任务列表
        """
        try:
            # 直接调用 self._task_repo.search_tasks
            tasks = self._task_repo.search_tasks(
                session,
                status=status,
                assignee=assignee,
                labels=labels,
                story_id=story_id,
                is_independent=is_independent,
                is_temporary=is_temporary,
                limit=limit,
                offset=offset,
            )

            # 转换为字典列表
            return [task.to_dict() if hasattr(task, "to_dict") else task for task in tasks]
        except Exception as e:
            logger.error(f"搜索任务失败: {e}", exc_info=True)
            return []

    def delete_task(self, task_id: str) -> bool:
        """删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        try:
            # 使用 session_scope 获取会话
            with session_scope() as session:
                # 直接调用仓库的删除方法
                return self._task_repo.delete(session, task_id)
        except ValueError:
            logger.warning(f"尝试删除不存在的任务 {task_id}")
            return False
        except Exception as e:
            logger.error(f"删除任务 {task_id} 失败: {e}")
            return False
