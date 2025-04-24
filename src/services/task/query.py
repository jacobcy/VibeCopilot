"""
任务查询服务模块

提供任务的查询、过滤等功能。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import get_session_factory

logger = logging.getLogger(__name__)


class TaskQueryService:
    """任务查询服务类，负责任务的查询和过滤操作"""

    def __init__(self, db_service):
        """初始化任务查询服务

        Args:
            db_service: 数据库服务实例
        """
        self._db_service = db_service
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
                with get_session_factory()() as session:
                    task = self._db_service.task_repo.get_by_id(session, current_task_id)
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
            # 使用 task_repo 获取任务
            task = self._db_service.task_repo.get_by_id(session, task_id)
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
            # 需要 session 来调用 get_task
            with get_session_factory()() as session:
                # 首先尝试通过ID查找
                task = self.get_task(session, identifier)
                if task:
                    return task

                # 如果找不到，尝试通过名称查找（不区分大小写）
                # 注意: list_tasks 也需要 session
                tasks = self.list_tasks(session=session)  # 假设 list_tasks 接受 session
                for task_item in tasks:
                    if task_item.get("title", "").lower() == identifier.lower():
                        return task_item

            # 都找不到，返回None
            return None
        except Exception as e:
            logger.error(f"通过标识符 {identifier} 查找任务失败: {e}")
            return None

    def list_tasks(
        self,
        session: Session,
        status: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        story_id: Optional[str] = None,
        is_independent: Optional[bool] = None,
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
            is_independent: 是否只返回独立任务
            limit: 返回结果数量限制
            offset: 结果偏移量

        Returns:
            任务列表
        """
        try:
            # 调用仓库层的 get_all 或 search_tasks 方法，传递 session
            # 假设 search_tasks 功能更全
            tasks = self._db_service.task_repo.search_tasks(
                session,
                status=status,
                assignee=assignee,
                labels=labels,
                roadmap_item_id=story_id,  # 假设 roadmap_item_id 对应 story_id
                is_independent=is_independent,
                # is_temporary 参数在 repo 中定义，这里没有传入，如有需要可添加
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
        roadmap_item_id: Optional[str] = None,
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
            roadmap_item_id: 关联的故事ID
            is_independent: 是否为独立任务
            is_temporary: 是否为临时任务
            limit: 限制数量
            offset: 偏移量

        Returns:
            符合条件的任务列表
        """
        try:
            # 直接调用仓库层的search_tasks方法，并传递 session
            tasks = self._db_service.task_repo.search_tasks(
                session,
                status=status,
                assignee=assignee,
                labels=labels,
                roadmap_item_id=roadmap_item_id,
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
            # 需要 session 来调用 get_task
            with get_session_factory()() as session:
                # 先检查任务是否存在
                existing_task = self.get_task(session, task_id)
                if not existing_task:
                    raise ValueError(f"任务 {task_id} 不存在")

                # 再执行删除，假设 delete_task 内部处理 session
                return self._db_service.delete_task(task_id)
        except Exception as e:
            logger.error(f"删除任务 {task_id} 失败: {e}")
            return False
