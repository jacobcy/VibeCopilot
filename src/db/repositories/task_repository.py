# src/db/repositories/task_repository.py

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from src.db.repository import Repository
from src.models.db.task import Task, TaskComment


class TaskRepository(Repository[Task]):
    """Task仓库"""

    def __init__(self, session: Session):
        super().__init__(session, Task)

    def create_task(self, data: Dict[str, Any]) -> Task:
        """创建任务，特殊处理 labels, linked_prs, linked_commits"""
        # 确保 labels 等是列表，如果提供了的话
        for field in ["labels", "linked_prs", "linked_commits"]:
            if field in data and data[field] is not None and not isinstance(data[field], list):
                # 可以添加更严格的类型检查或转换逻辑
                raise ValueError(f"字段 '{field}' 必须是列表或 None")
        return self.create(data)

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Optional[Task]:
        """更新任务，特殊处理 labels, linked_prs, linked_commits"""
        # 确保 labels 等是列表，如果提供了的话
        for field in ["labels", "linked_prs", "linked_commits"]:
            if field in data and data[field] is not None and not isinstance(data[field], list):
                raise ValueError(f"字段 '{field}' 必须是列表或 None")

        # 更新 updated_at 时间戳
        data["updated_at"] = datetime.utcnow()

        # 如果状态变为 closed，记录 closed_at 时间
        if "status" in data and data["status"] in ["closed", "done"] and data.get("closed_at") is None:
            existing_task = self.get_by_id(task_id)
            if existing_task and existing_task.status not in ["closed", "done"]:
                data["closed_at"] = datetime.utcnow()
        elif "status" in data and data["status"] not in ["closed", "done"]:
            data["closed_at"] = None  # 如果从 closed/done 切换回 open/in_progress，清除 closed_at

        return self.update(task_id, data)

    def get_by_id_with_comments(self, task_id: str) -> Optional[Task]:
        """获取任务及其所有评论"""
        return self.session.query(Task).options(joinedload(Task.comments)).filter(Task.id == task_id).first()

    def search_tasks(
        self,
        status: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        roadmap_item_id: Optional[str] = None,
        workflow_session_id: Optional[str] = None,
        workflow_stage_instance_id: Optional[str] = None,
        is_independent: Optional[bool] = None,  # True: 只返回无roadmap关联的任务, False: 只返回有关联的任务
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Task]:
        """根据多种条件搜索任务"""
        query = self.session.query(Task)

        if status:
            query = query.filter(Task.status.in_(status))
        if assignee:
            query = query.filter(Task.assignee == assignee)
        if roadmap_item_id:
            query = query.filter(Task.roadmap_item_id == roadmap_item_id)
        if workflow_session_id:
            query = query.filter(Task.workflow_session_id == workflow_session_id)
        if workflow_stage_instance_id:
            query = query.filter(Task.workflow_stage_instance_id == workflow_stage_instance_id)

        if is_independent is True:
            query = query.filter(Task.roadmap_item_id.is_(None))
        elif is_independent is False:
            query = query.filter(Task.roadmap_item_id.isnot(None))

        # 搜索 labels (JSON 包含查询) - 不同数据库实现可能不同
        # 简单的实现（性能可能不高）：
        if labels:
            # 注意：这种方式需要 labels 列表中的所有标签都存在于 Task.labels 中
            # 并且依赖于数据库对 JSON 的支持和查询方式
            # for label in labels:
            #    query = query.filter(Task.labels.contains(label)) # SQLAlchemy >= 1.4
            # 或者更通用的（但可能是字符串匹配）:
            # query = query.filter(Task.labels.astext.like(f'%"{label}"%'))
            # 更好的方式是使用数据库特定的 JSON 函数，或将标签存储在关联表中
            # 为了演示，这里省略复杂的 JSON 查询
            pass

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        return query.order_by(Task.created_at.desc()).all()

    def link_to_roadmap(self, task_id: str, roadmap_item_id: Optional[str]) -> Optional[Task]:
        """关联或取消关联任务到 Roadmap Item"""
        return self.update_task(task_id, {"roadmap_item_id": roadmap_item_id})

    def link_to_workflow_session(self, task_id: str, workflow_session_id: Optional[str]) -> Optional[Task]:
        """关联或取消关联任务到 Workflow Session"""
        return self.update_task(task_id, {"workflow_session_id": workflow_session_id})

    def link_to_workflow_stage(self, task_id: str, workflow_stage_instance_id: Optional[str]) -> Optional[Task]:
        """关联或取消关联任务到 Workflow Stage Instance"""
        return self.update_task(task_id, {"workflow_stage_instance_id": workflow_stage_instance_id})

    def link_to_github_issue(self, task_id: str, issue_number: Optional[int]) -> Optional[Task]:
        """关联或取消关联任务到 GitHub Issue"""
        return self.update_task(task_id, {"github_issue_number": issue_number})

    def add_linked_pr(self, task_id: str, repo: str, pr_number: int) -> Optional[Task]:
        """添加关联的 Pull Request"""
        task = self.get_by_id(task_id)
        if not task:
            return None
        linked_prs = task.linked_prs or []
        new_pr = {"repo": repo, "pr_number": pr_number}
        if new_pr not in linked_prs:
            linked_prs.append(new_pr)
            return self.update_task(task_id, {"linked_prs": linked_prs})
        return task

    def remove_linked_pr(self, task_id: str, repo: str, pr_number: int) -> Optional[Task]:
        """移除关联的 Pull Request"""
        task = self.get_by_id(task_id)
        if not task or not task.linked_prs:
            return task
        linked_prs = task.linked_prs
        pr_to_remove = {"repo": repo, "pr_number": pr_number}
        if pr_to_remove in linked_prs:
            linked_prs.remove(pr_to_remove)
            return self.update_task(task_id, {"linked_prs": linked_prs})
        return task

    def add_linked_commit(self, task_id: str, repo: str, sha: str) -> Optional[Task]:
        """添加关联的 Commit"""
        task = self.get_by_id(task_id)
        if not task:
            return None
        linked_commits = task.linked_commits or []
        new_commit = {"repo": repo, "sha": sha}
        if new_commit not in linked_commits:
            linked_commits.append(new_commit)
            return self.update_task(task_id, {"linked_commits": linked_commits})
        return task

    def remove_linked_commit(self, task_id: str, repo: str, sha: str) -> Optional[Task]:
        """移除关联的 Commit"""
        task = self.get_by_id(task_id)
        if not task or not task.linked_commits:
            return task
        linked_commits = task.linked_commits
        commit_to_remove = {"repo": repo, "sha": sha}
        if commit_to_remove in linked_commits:
            linked_commits.remove(commit_to_remove)
            return self.update_task(task_id, {"linked_commits": linked_commits})
        return task


class TaskCommentRepository(Repository[TaskComment]):
    """TaskComment仓库"""

    def __init__(self, session: Session):
        super().__init__(session, TaskComment)

    def get_comments_for_task(self, task_id: str, limit: Optional[int] = None, offset: Optional[int] = None) -> List[TaskComment]:
        """获取指定任务的所有评论"""
        query = self.session.query(TaskComment).filter(TaskComment.task_id == task_id)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.order_by(TaskComment.created_at.asc()).all()

    def add_comment(self, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """为任务添加评论"""
        comment_data = {"task_id": task_id, "content": content, "author": author}
        return self.create(comment_data)
