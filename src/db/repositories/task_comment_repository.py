"""
任务评论仓库
"""

from typing import List, Optional

from src.db.models.task_comment import TaskComment
from src.db.repositories.base_repository import BaseRepository


class TaskCommentRepository(BaseRepository):
    """任务评论仓库类"""

    def __init__(self, session):
        super().__init__(session, TaskComment)

    def get_by_task_id(self, task_id: int) -> List[TaskComment]:
        """获取指定任务的所有评论

        Args:
            task_id: 任务ID

        Returns:
            List[TaskComment]: 评论列表
        """
        return self.session.query(self.model).filter(self.model.task_id == task_id).all()

    def create_comment(self, task_id: int, content: str) -> TaskComment:
        """创建新的任务评论

        Args:
            task_id: 任务ID
            content: 评论内容

        Returns:
            TaskComment: 创建的评论对象
        """
        comment = TaskComment(task_id=task_id, content=content)
        self.session.add(comment)
        self.session.commit()
        return comment
