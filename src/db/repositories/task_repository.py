# src/db/repositories/task_repository.py

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from src.db.repository import Repository
from src.models.db import Task, TaskComment

logger = logging.getLogger(__name__)


class TaskRepository(Repository[Task]):
    """Task仓库"""

    def __init__(self, session: Session):
        super().__init__(session, Task)
        self.logger = logger

    def create_task(self, data: Dict[str, Any]) -> Task:
        """创建任务，特殊处理 labels, linked_prs, linked_commits"""
        # 确保 labels 等是列表，如果提供了的话
        for field in ["labels", "linked_prs", "linked_commits"]:
            if field in data and data[field] is not None and not isinstance(data[field], list):
                # 可以添加更严格的类型检查或转换逻辑
                raise ValueError(f"字段 '{field}' 必须是列表或 None")

        # 检查Task模型是否有特定属性，如果没有则从数据中删除
        for field in ["roadmap_item_id", "workflow_stage_instance_id", "github_issue_number"]:
            if not hasattr(Task, field) and field in data:
                logger.warning(f"Task模型没有{field}属性，已从创建数据中删除")
                data.pop(field)

        return self.create(data)

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Optional[Task]:
        """更新任务，特殊处理 labels, linked_prs, linked_commits"""
        # 确保 labels 等是列表，如果提供了的话
        for field in ["labels", "linked_prs", "linked_commits"]:
            if field in data and data[field] is not None and not isinstance(data[field], list):
                raise ValueError(f"字段 '{field}' 必须是列表或 None")

        # 检查Task模型是否有特定属性，如果没有则从数据中删除
        for field in ["roadmap_item_id", "workflow_stage_instance_id", "github_issue_number"]:
            if not hasattr(Task, field) and field in data:
                logger.warning(f"Task模型没有{field}属性，已从更新数据中删除")
                data.pop(field)

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
        is_independent: Optional[bool] = None,  # True: 只返回无roadmap关联的任务, False: 只返回有关联的任务
        is_temporary: Optional[bool] = None,  # True: 只返回临时任务(无story_id), False: 只返回正式任务(有story_id)
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Task]:
        """根据多种条件搜索任务"""
        query = self.session.query(Task)

        if status:
            query = query.filter(Task.status.in_(status))
        if assignee:
            query = query.filter(Task.assignee == assignee)

        # 使用story_id字段来区分临时任务和正式任务
        if is_temporary is True:
            # 临时任务：没有story_id的任务
            query = query.filter(Task.story_id.is_(None))
        elif is_temporary is False:
            # 正式任务：有story_id的任务
            query = query.filter(Task.story_id.isnot(None))
        # 如果is_temporary是None，则不过滤，显示所有任务

        # 兼容旧的is_independent参数，将其映射到is_temporary
        if is_independent is not None and is_temporary is None:
            logger.info(f"使用is_independent={is_independent}参数，映射到is_temporary")
            if is_independent is True:
                # 独立任务就是临时任务
                query = query.filter(Task.story_id.is_(None))
            # 不再默认过滤非独立任务，只有当明确指定is_independent=False时才过滤
            # 这样默认情况下会显示所有任务

        # 兼容roadmap_item_id参数，如果有的话，尝试使用story_id过滤
        if roadmap_item_id:
            # 假设 roadmap_item_id 就是 story_id
            logger.info(f"使用roadmap_item_id={roadmap_item_id}参数，映射到story_id")
            query = query.filter(Task.story_id == roadmap_item_id)

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

        # 添加调试日志
        print(f"Task查询SQL: {query}")
        results = query.all()
        print(f"查询到 {len(results)} 个任务")
        for task in results:
            print(f"Task: {task.id}, {task.title}, story_id={task.story_id}")
        return results

    def link_to_roadmap(self, task_id: str, roadmap_item_id: Optional[str]) -> Optional[Task]:
        """关联或取消关联任务到 Roadmap Item

        在简化方案中，我们将roadmap_item_id映射到story_id
        """
        logger.info(f"将任务 {task_id} 关联到路线图项 {roadmap_item_id}，映射到story_id")
        return self.update_task(task_id, {"story_id": roadmap_item_id})

    def link_to_workflow_stage(self, task_id: str, workflow_stage_instance_id: Optional[str]) -> Optional[Task]:
        """关联或取消关联任务到 Workflow Stage Instance"""
        # 检查Task模型是否有workflow_stage_instance_id属性
        if hasattr(Task, "workflow_stage_instance_id"):
            return self.update_task(task_id, {"workflow_stage_instance_id": workflow_stage_instance_id})
        else:
            logger.warning("Task模型没有workflow_stage_instance_id属性，无法关联到工作流阶段")
            # 返回未修改的任务
            return self.get_by_id(task_id)

    def link_to_github_issue(self, task_id: str, issue_number: Optional[int]) -> Optional[Task]:
        """关联或取消关联任务到 GitHub Issue"""
        # 检查Task模型是否有github_issue_number属性
        if hasattr(Task, "github_issue_number"):
            return self.update_task(task_id, {"github_issue_number": issue_number})
        else:
            logger.warning("Task模型没有github_issue_number属性，无法关联到GitHub Issue")
            # 返回未修改的任务
            return self.get_by_id(task_id)

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

    def get_by_story_id(self, story_id: str) -> List[Task]:
        """根据故事ID获取任务列表

        Args:
            story_id: 故事ID

        Returns:
            List[Task]: 任务列表
        """
        return self.session.query(Task).filter(Task.story_id == story_id).all()

    def get_by_roadmap_id(self, roadmap_id: str) -> List[Task]:
        """获取指定路线图的所有任务

        Args:
            roadmap_id: 路线图ID

        Returns:
            List[Task]: 任务列表
        """
        try:
            # 通过Story和Epic关联查询
            from src.models.db import Epic, Story

            tasks = (
                self.session.query(Task)
                .join(Story, Task.story_id == Story.id)
                .join(Epic, Story.epic_id == Epic.id)
                .filter(Epic.roadmap_id == roadmap_id)
                .all()
            )

            self.logger.info(f"从路线图 {roadmap_id} 找到 {len(tasks)} 个任务")
            return tasks

        except Exception as e:
            self.logger.error(f"获取路线图任务时出错: {e}")
            return []


class TaskCommentRepository(Repository[TaskComment]):
    """TaskComment仓库"""

    def __init__(self, session: Session):
        super().__init__(session, TaskComment)
        self.logger = logger

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
