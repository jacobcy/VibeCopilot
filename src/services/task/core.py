"""
任务服务核心模块

提供TaskService类的主要实现，包括初始化和基本操作。
"""

import logging
import uuid
from typing import Any, Dict, Optional

from loguru import logger

from src.db.service import DatabaseService
from src.services.task.comment import TaskCommentService
from src.services.task.query import TaskQueryService
from src.services.task.session import TaskSessionService

logger = logging.getLogger(__name__)


class TaskService:
    """任务服务类，整合任务相关的业务逻辑

    提供任务的创建、查询、更新、删除等功能，封装底层数据访问操作，
    并实现任务相关的业务规则和校验逻辑。
    """

    def __init__(self):
        self._db_service = DatabaseService()
        # 获取状态服务实例
        from src.status.service import StatusService

        self._status_service = StatusService.get_instance()

        # 初始化子服务
        self._comment_service = TaskCommentService(self._db_service)
        self._query_service = TaskQueryService(self._db_service)
        self._session_service = TaskSessionService(self._db_service, self._status_service)

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """获取当前任务"""
        return self._query_service.get_current_task()

    def set_current_task(self, task_id: str) -> bool:
        """设置当前任务

        设置指定任务为当前任务，同时如果任务有关联的会话，将该会话设置为当前会话。
        """
        return self._session_service.set_current_task(task_id)

    def create_task(self, title: str, story_id: str = None, github_issue: str = None) -> Optional[Dict[str, Any]]:
        """创建新任务"""
        try:
            task = self._db_service.task_repo.create({"title": title, "status": "created", "story_id": story_id, "github_issue": github_issue})
            return task.to_dict() if task else None
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return None

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新任务信息"""
        try:
            task = self._db_service.task_repo.update_task(task_id, data)
            return task.to_dict() if task else None
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return None

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        return self._query_service.get_task(task_id)

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        return self._query_service.delete_task(task_id)

    def link_task(self, task_id: str, link_type: str, target_id: str) -> bool:
        """关联任务到其他实体"""
        try:
            # 先检查任务是否存在
            existing_task = self.get_task(task_id)
            if not existing_task:
                raise ValueError(f"任务 {task_id} 不存在")

            # 根据关联类型确定更新字段
            update_data = {}

            if link_type == "story":
                update_data["story_id"] = target_id
            elif link_type == "flow":
                update_data["flow_session_id"] = target_id
            elif link_type == "github":
                update_data["github_issue_number"] = target_id
            else:
                raise ValueError(f"不支持的关联类型: {link_type}")

            # 执行更新
            result = self.update_task(task_id, update_data)
            return result is not None
        except Exception as e:
            logger.error(f"关联任务 {task_id} 到 {link_type}:{target_id} 失败: {e}")
            return False

    # 任务评论相关方法代理
    def add_task_comment(self, task_id: str, comment: str, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """添加任务评论"""
        return self._comment_service.add_task_comment(task_id, comment, author)

    # 任务会话相关方法代理
    def link_to_flow_session(self, task_id: str, flow_type: str = None, session_id: str = None) -> Optional[Dict[str, Any]]:
        """关联任务到工作流会话"""
        return self._session_service.link_to_flow_session(task_id, flow_type, session_id)

    def create_task_with_flow(self, task_data: Dict[str, Any], workflow_id: str) -> Optional[Dict[str, Any]]:
        """创建任务并自动关联工作流会话"""
        return self._session_service.create_task_with_flow(self, task_data, workflow_id)

    def get_task_sessions(self, task_id: str):
        """获取任务关联的所有工作流会话"""
        return self._session_service.get_task_sessions(task_id)

    def get_current_task_session(self):
        """获取当前任务的当前工作流会话"""
        return self._session_service.get_current_task_session()

    def set_current_task_session(self, session_id: str) -> bool:
        """设置当前任务的当前工作流会话"""
        return self._session_service.set_current_task_session(session_id)
