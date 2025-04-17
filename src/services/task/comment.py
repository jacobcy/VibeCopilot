"""
任务评论服务模块

提供任务评论的添加和查询功能。
"""

import logging
from typing import Any, Dict, List, Optional

from src.db.service import DatabaseService

logger = logging.getLogger(__name__)


class TaskCommentService:
    """任务评论服务类，负责任务评论的添加和查询操作"""

    def __init__(self, db_service: DatabaseService):
        """初始化任务评论服务

        Args:
            db_service: 数据库服务实例
        """
        self._db_service = db_service

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
            # 创建评论数据
            comment_data = {"task_id": task_id, "content": comment, "author": author or "AI Agent"}

            # 创建评论
            comment = self._db_service.task_comment_repo.create(comment_data)
            return comment.to_dict() if comment else None
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
            # 获取评论列表
            comments = self._db_service.task_comment_repo.get_by_task_id(task_id)
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
            return self._db_service.task_comment_repo.delete(comment_id)
        except Exception as e:
            logger.error(f"删除任务评论失败: {e}")
            return False
