"""
任务评论服务模块

提供任务评论的添加和查询功能。
"""

import logging
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TaskCommentService:
    """任务评论服务类，负责任务评论的添加和查询操作"""

    def __init__(self, db_service):
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
            author: 评论作者

        Returns:
            添加的评论信息，失败返回None
        """
        try:
            # 先检查任务是否存在
            task = self._db_service.get_task(task_id)
            if not task:
                raise ValueError(f"任务 {task_id} 不存在")

            # 假设有一个添加评论的方法
            # 注意：这里简化处理，实际实现可能需要调用特定的评论仓库或方法
            comment_data = {"id": f"comment_{uuid.uuid4().hex[:8]}", "task_id": task_id, "content": comment, "author": author or "系统"}

            # 这里需要根据实际的数据库服务接口调整
            # 假设有一个create_task_comment方法
            result = self._db_service.create_entity("task_comment", comment_data)
            return result
        except Exception as e:
            logger.error(f"为任务 {task_id} 添加评论失败: {e}")
            return None

    def get_task_comments(self, task_id: str, limit: Optional[int] = None, offset: Optional[int] = None):
        """获取任务的评论列表

        Args:
            task_id: 任务ID
            limit: 返回结果数量限制
            offset: 结果偏移量

        Returns:
            评论列表
        """
        try:
            # 这个方法需要在数据库服务中实现
            return self._db_service.get_task_comments(task_id, limit, offset)
        except Exception as e:
            logger.error(f"获取任务 {task_id} 的评论失败: {e}")
            return []
