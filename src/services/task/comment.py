"""
任务评论服务模块

提供任务评论的添加和查询功能。
"""

import logging
from typing import Any, Dict, List, Optional

from src.db.repositories.task_repository import TaskCommentRepository
from src.db.session_manager import session_scope
from src.models.db.task import TaskComment

logger = logging.getLogger(__name__)


class TaskCommentService:
    """任务评论服务类，负责任务评论的添加和查询操作"""

    def __init__(self):
        """初始化任务评论服务"""
        self._task_comment_repo = TaskCommentRepository()

    def add_task_comment(self, task_id: str, comment: str, author: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """添加任务评论

        Args:
            task_id: 任务ID
            comment: 评论内容
            author: 评论作者（可选）

        Returns:
            评论数据字典，如果失败则返回None
        """
        try:
            comment_data = {"task_id": task_id, "content": comment, "author": author or "AI Agent"}
            with session_scope() as session:
                created_comment = self._task_comment_repo.create(session=session, **comment_data)
                return created_comment.to_dict() if created_comment else None
        except Exception as e:
            logger.error(f"添加任务评论失败: {e}")
            return None

    def get_task_comments(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的所有评论

        Args:
            task_id: 任务ID

        Returns:
            评论数据字典列表
        """
        try:
            with session_scope() as session:
                comments = self._task_comment_repo.get_by_task_id(session=session, task_id=task_id)
                return [comment.to_dict() for comment in comments] if comments else []
        except Exception as e:
            logger.error(f"获取任务评论失败: {e}")
            return []

    def delete_task_comment(self, comment_id: str) -> bool:
        """删除任务评论

        Args:
            comment_id: 评论ID

        Returns:
            是否删除成功
        """
        try:
            with session_scope() as session:
                return self._task_comment_repo.delete(session=session, comment_id=comment_id)
        except Exception as e:
            logger.error(f"删除任务评论失败: {e}")
            return False
