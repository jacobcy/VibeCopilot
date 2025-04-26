# src/db/repositories/task_repository.py

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from src.db.repository import Repository
from src.models.db import Task, TaskComment
from src.utils.id_generator import EntityType, IdGenerator

logger = logging.getLogger(__name__)


class TaskRepository(Repository[Task]):
    """Task仓库"""

    def __init__(self):
        super().__init__(Task)
        self.logger = logger

    def create(self, session: Session, **data: Any) -> Task:
        """创建 Task (覆盖基类方法以处理ID和默认值)"""
        if "id" not in data:
            data["id"] = IdGenerator.generate_task_id()

        # Set default values if not provided
        now_iso = datetime.utcnow().isoformat()
        data.setdefault("status", "todo")
        data.setdefault("priority", "medium")
        data.setdefault("description", "")
        data.setdefault("labels", [])
        data.setdefault("created_at", now_iso)
        data.setdefault("updated_at", now_iso)
        data.setdefault("memory_references", [])

        # Model's __init__ handles defaults too, this provides primary defaults

        entity = self.model_class(**data)
        session.add(entity)
        return entity

    def update_task(self, session: Session, task_id: str, data: Dict[str, Any]) -> Optional[Task]:
        """更新任务，特殊处理 labels, linked_prs, linked_commits"""
        # 确保 labels 等是列表，如果提供了的话
        for field in ["labels", "linked_prs", "linked_commits"]:
            if field in data and data[field] is not None and not isinstance(data[field], list):
                # Allow clearing with None
                if data[field] is None:
                    continue
                raise ValueError(f"字段 '{field}' 必须是列表或 None")

        # 检查Task模型是否有特定属性，如果没有则从数据中删除
        for field in ["roadmap_item_id", "workflow_stage_instance_id", "github_issue_number"]:
            if not hasattr(Task, field) and field in data:
                logger.warning(f"Task模型没有{field}属性，已从更新数据中删除")
                data.pop(field)

        # 更新 updated_at 时间戳
        data["updated_at"] = datetime.utcnow().isoformat()

        # 如果状态变为 closed，记录 closed_at 时间
        if "status" in data and data["status"] in ["closed", "done"] and data.get("closed_at") is None:
            existing_task = self.get_by_id(session, task_id)
            # Only set closed_at if it's newly closed and closed_at exists on model
            if existing_task and existing_task.status not in ["closed", "done"] and hasattr(Task, "closed_at"):
                data["closed_at"] = datetime.utcnow().isoformat()
        elif "status" in data and data["status"] not in ["closed", "done"]:
            # Clear closed_at if status changes back from closed/done
            if hasattr(Task, "closed_at"):
                data["closed_at"] = None

        return self.update(session, task_id, data)  # Use the generic update

    def get_by_id(self, session: Session, entity_id: str) -> Optional[Task]:
        """通过ID获取任务 (覆盖或实现基类方法)"""
        return session.query(self.model_class).filter(self.model_class.id == entity_id).first()

    def get_by_id_with_comments(self, session: Session, task_id: str) -> Optional[Task]:
        """获取任务及其所有评论"""
        return session.query(Task).options(joinedload(Task.comments)).filter(Task.id == task_id).first()

    def search_tasks(
        self,
        session: Session,
        status: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        story_id: Optional[str] = None,  # Explicitly add story_id
        roadmap_item_id: Optional[str] = None,  # Deprecated
        is_independent: Optional[bool] = None,  # Deprecated
        is_temporary: Optional[bool] = None,  # Preferred over is_independent
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Task]:
        """根据多种条件搜索任务"""
        query = session.query(Task)

        if status:
            query = query.filter(Task.status.in_(status))
        if assignee:
            query = query.filter(Task.assignee == assignee)

        # --- Refined filtering logic ---
        # Prioritize explicit story_id if provided
        if story_id is not None:
            query = query.filter(Task.story_id == story_id)
        # Use deprecated roadmap_item_id only if story_id is not given
        elif roadmap_item_id is not None:
            logger.warning("Using deprecated 'roadmap_item_id' for Task search, mapping to 'story_id'. Please update calls to use 'story_id'.")
            query = query.filter(Task.story_id == roadmap_item_id)

        # Prioritize is_temporary over is_independent
        if is_temporary is True:
            query = query.filter(Task.story_id.is_(None))
        elif is_temporary is False:
            query = query.filter(Task.story_id.isnot(None))
        # Use deprecated is_independent only if is_temporary is not given
        elif is_independent is True:
            logger.warning(
                "Using deprecated 'is_independent=True' for Task search, mapping to 'story_id is None'. Please update calls to use 'is_temporary=True'."
            )
            query = query.filter(Task.story_id.is_(None))
        elif is_independent is False:
            logger.warning(
                "Using deprecated 'is_independent=False' for Task search, mapping to 'story_id is not None'. Please update calls to use 'is_temporary=False'."
            )
            query = query.filter(Task.story_id.isnot(None))
        # ---------------------------------

        # Labels search remains complex and DB-dependent
        if labels:
            logger.warning("Label search in TaskRepository.search_tasks is currently not implemented.")
            # Placeholder for actual implementation if needed later
            pass

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        results = query.all()
        return results

    def exists_with_title(self, session: Session, title: str) -> bool:
        """检查是否存在具有完全相同标题的任务"""
        # 使用 exists() 和 literal() 来生成更高效的 SQL 查询
        # SELECT EXISTS (SELECT 1 FROM tasks WHERE tasks.title = ?) -- 类似这样
        return session.query(session.query(Task).filter(Task.title == title).exists()).scalar()

    def get_by_title_and_story_id(self, session: Session, title: str, story_id: str) -> Optional[Task]:
        """根据标题和 Story ID 获取任务"""
        if not story_id:  # Avoid querying with None story_id
            logger.warning("Attempted to get task by title with None story_id.")
            return None
        return session.query(self.model_class).filter(self.model_class.title == title, self.model_class.story_id == story_id).first()

    def link_to_roadmap(self, session: Session, task_id: str, roadmap_item_id: Optional[str]) -> Optional[Task]:
        """关联或取消关联任务到 Roadmap Item (映射到 story_id)"""
        logger.info(f"将任务 {task_id} 关联到路线图项 {roadmap_item_id}，映射到story_id")
        # Use update_task for consistency
        return self.update_task(session, task_id, {"story_id": roadmap_item_id})

    def link_to_workflow_stage(self, session: Session, task_id: str, workflow_stage_instance_id: Optional[str]) -> Optional[Task]:
        """关联或取消关联任务到 Workflow Stage Instance"""
        if hasattr(Task, "workflow_stage_instance_id"):
            return self.update_task(session, task_id, {"workflow_stage_instance_id": workflow_stage_instance_id})
        else:
            logger.warning("Task模型没有workflow_stage_instance_id属性，无法关联到工作流阶段")
            return self.get_by_id(session, task_id)

    def link_to_github_issue(self, session: Session, task_id: str, issue_number: Optional[int]) -> Optional[Task]:
        """关联或取消关联任务到 GitHub Issue"""
        if hasattr(Task, "github_issue_number"):
            return self.update_task(session, task_id, {"github_issue_number": issue_number})
        else:
            logger.warning("Task模型没有github_issue_number属性，无法关联到GitHub Issue")
            return self.get_by_id(session, task_id)

    def add_linked_pr(self, session: Session, task_id: str, repo: str, pr_number: int) -> Optional[Task]:
        """添加关联的 Pull Request"""
        task = self.get_by_id(session, task_id)
        if not task:
            return None
        # Ensure linked_prs exists and is a list
        linked_prs = getattr(task, "linked_prs", []) or []
        if not isinstance(linked_prs, list):
            linked_prs = []  # Handle potential non-list data if loaded incorrectly

        new_pr = {"repo": repo, "pr_number": pr_number}
        if new_pr not in linked_prs:
            # Create a new list to ensure mutation detection by SQLAlchemy
            updated_prs = linked_prs + [new_pr]
            return self.update_task(session, task_id, {"linked_prs": updated_prs})
        return task  # Return unmodified task if PR already linked

    def remove_linked_pr(self, session: Session, task_id: str, repo: str, pr_number: int) -> Optional[Task]:
        """移除关联的 Pull Request"""
        task = self.get_by_id(session, task_id)
        if not task:
            return None
        linked_prs = getattr(task, "linked_prs", []) or []
        if not isinstance(linked_prs, list):
            linked_prs = []

        pr_to_remove = {"repo": repo, "pr_number": pr_number}
        # Create a new list excluding the PR to remove
        updated_prs = [pr for pr in linked_prs if pr != pr_to_remove]

        # Only update if the list actually changed
        if len(updated_prs) < len(linked_prs):
            return self.update_task(session, task_id, {"linked_prs": updated_prs})
        return task  # Return unmodified task if PR not found

    def add_linked_commit(self, session: Session, task_id: str, repo: str, sha: str) -> Optional[Task]:
        """添加关联的 Commit"""
        task = self.get_by_id(session, task_id)
        if not task:
            return None
        linked_commits = getattr(task, "linked_commits", []) or []
        if not isinstance(linked_commits, list):
            linked_commits = []

        new_commit = {"repo": repo, "sha": sha}
        if new_commit not in linked_commits:
            updated_commits = linked_commits + [new_commit]
            return self.update_task(session, task_id, {"linked_commits": updated_commits})
        return task

    def remove_linked_commit(self, session: Session, task_id: str, repo: str, sha: str) -> Optional[Task]:
        """移除关联的 Commit"""
        task = self.get_by_id(session, task_id)
        if not task:
            return None
        linked_commits = getattr(task, "linked_commits", []) or []
        if not isinstance(linked_commits, list):
            linked_commits = []

        commit_to_remove = {"repo": repo, "sha": sha}
        updated_commits = [commit for commit in linked_commits if commit != commit_to_remove]

        if len(updated_commits) < len(linked_commits):
            return self.update_task(session, task_id, {"linked_commits": updated_commits})
        return task

    def get_by_story_id(self, session: Session, story_id: str) -> List[Task]:
        """根据 Story ID 获取所有关联的任务"""
        return session.query(Task).filter(Task.story_id == story_id).all()

    def get_by_roadmap_id(self, session: Session, roadmap_id: str) -> List[Task]:
        """
        获取指定路线图下的所有任务 (通过 Story -> Epic 关联)。
        注意: 这不会获取没有关联到 Story 的任务。
        """
        from src.models.db import Epic, Story  # Import locally to avoid circular dependency potential

        try:
            return (
                session.query(Task)
                .options(joinedload(Task.story))
                .join(Story, Task.story_id == Story.id)
                .join(Epic, Story.epic_id == Epic.id)
                .filter(Epic.roadmap_id == roadmap_id)
                .all()
            )
        except Exception as e:
            logger.error(f"获取路线图 {roadmap_id} 的任务时出错: {e}", exc_info=True)
            return []

    def add_memory_reference(self, session: Session, task_id: str, permalink: str, title: str, added_at: Optional[str] = None) -> Optional[Task]:
        """
        向任务添加记忆引用

        Args:
            session: SQLAlchemy会话
            task_id: 任务ID
            permalink: 记忆项的永久链接 (例如 'memory://notes/folder/note_title')
            title: 记忆项的标题
            added_at: 添加时间 (ISO格式字符串)，默认为当前时间

        Returns:
            更新后的Task对象或None
        """
        task = self.get_by_id(session, task_id)
        if not task:
            return None

        # 确保 memory_references 是一个列表
        memory_refs = getattr(task, "memory_references", []) or []
        if not isinstance(memory_refs, list):
            logger.warning(f"Task {task_id} 的 memory_references 不是列表，将被重置。")
            memory_refs = []

        # 检查引用是否已存在
        if any(ref.get("permalink") == permalink for ref in memory_refs):
            logger.debug(f"记忆引用 '{permalink}' 已存在于任务 {task_id}")
            return task  # 已存在，无需添加

        # 添加新引用
        new_ref = {
            "permalink": permalink,
            "title": title,
            "added_at": added_at or datetime.utcnow().isoformat(),
        }
        # 创建新列表以触发SQLAlchemy的变更检测
        updated_refs = memory_refs + [new_ref]

        # 调用 update_task 更新任务
        return self.update_task(session, task_id, {"memory_references": updated_refs})

    def remove_memory_reference(self, session: Session, task_id: str, permalink: str) -> Optional[Task]:
        """
        从任务中移除记忆引用

        Args:
            session: SQLAlchemy会话
            task_id: 任务ID
            permalink: 要移除的记忆项的永久链接

        Returns:
            更新后的Task对象或None
        """
        task = self.get_by_id(session, task_id)
        if not task:
            return None

        memory_refs = getattr(task, "memory_references", []) or []
        if not isinstance(memory_refs, list):
            return task  # 不是列表，无法移除

        # 创建不包含要移除引用的新列表
        updated_refs = [ref for ref in memory_refs if ref.get("permalink") != permalink]

        # 如果列表发生变化，则更新
        if len(updated_refs) < len(memory_refs):
            logger.info(f"从任务 {task_id} 移除记忆引用: {permalink}")
            return self.update_task(session, task_id, {"memory_references": updated_refs})
        else:
            logger.debug(f"未在任务 {task_id} 中找到要移除的记忆引用: {permalink}")
            return task  # 未找到，返回原始任务

    def get_memory_references(self, session: Session, task_id: str) -> List[Dict[str, Any]]:
        """
        获取任务的所有记忆引用

        Args:
            session: SQLAlchemy会话
            task_id: 任务ID

        Returns:
            记忆引用列表，如果任务不存在或没有引用则返回空列表
        """
        task = self.get_by_id(session, task_id)
        if not task:
            return []

        memory_refs = getattr(task, "memory_references", []) or []
        if not isinstance(memory_refs, list):
            logger.warning(f"Task {task_id} 的 memory_references 数据损坏 (非列表)，返回空列表。")
            return []

        return memory_refs


class TaskCommentRepository(Repository[TaskComment]):
    """任务评论仓库"""

    def __init__(self):
        super().__init__(TaskComment)

    def get_comments_for_task(self, session: Session, task_id: str, limit: Optional[int] = None, offset: Optional[int] = None) -> List[TaskComment]:
        """获取指定任务的评论"""
        query = session.query(TaskComment).filter(TaskComment.task_id == task_id).order_by(TaskComment.created_at.desc())
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()

    def add_comment(self, session: Session, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """添加评论到任务"""
        # 检查任务是否存在
        task_exists = session.query(Task.id).filter(Task.id == task_id).scalar() is not None
        if not task_exists:
            raise ValueError(f"任务不存在: {task_id}")

        comment = TaskComment(
            task_id=task_id,
            content=content,
            author=author or "System",
            # __init__ handles ID and created_at
        )
        session.add(comment)
        # session_scope handles commit/flush
        return comment
