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

    def create_task(
        self,
        session: Session,
        title: str,
        description: Optional[str] = None,
        status: str = "open",
        priority: str = "medium",
        assignee: Optional[str] = None,
        story_id: Optional[str] = None,
        labels: Optional[List[str]] = None,
        due_date: Optional[str] = None,
    ) -> Task:
        """创建任务

        Args:
            title: 任务标题
            description: 任务描述
            status: 任务状态
            priority: 任务优先级
            assignee: 任务负责人
            story_id: 关联的故事ID
            labels: 标签列表
            due_date: 截止日期

        Returns:
            Task: 创建的任务
        """
        # 使用ID生成器生成标准格式的ID
        task_id = IdGenerator.generate_task_id()

        # 准备任务数据
        now = datetime.utcnow()

        # 如果未设置截止日期，默认为3天后
        if due_date is None:
            due_date = (now + timedelta(days=3)).isoformat()

        # 创建新的Task实例
        task = Task(
            id=task_id,
            title=title,
            description=description or "",
            status=status,
            priority=priority,
            assignee=assignee,
            story_id=story_id,
            labels=labels or [],
            due_date=due_date,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
        )

        # 将任务添加到会话并返回
        session.add(task)
        return task

    def update_task(self, session: Session, task_id: str, data: Dict[str, Any]) -> Optional[Task]:
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
            existing_task = self.get_by_id(session, task_id)
            if existing_task and existing_task.status not in ["closed", "done"]:
                data["closed_at"] = datetime.utcnow()
        elif "status" in data and data["status"] not in ["closed", "done"]:
            data["closed_at"] = None  # 如果从 closed/done 切换回 open/in_progress，清除 closed_at

        return self.update(session, task_id, data)

    def get_by_id(self, session: Session, entity_id: str) -> Optional[Task]:
        """通过ID获取任务 (覆盖或实现基类方法)"""
        return session.query(self.model_class).filter(self.model_class.id == entity_id).first()

    def update(self, session: Session, entity_id: str, data: Dict[str, Any]) -> Optional[Task]:
        """通过ID更新任务 (覆盖或实现基类方法)"""
        entity = self.get_by_id(session, entity_id)
        if entity:
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
                else:
                    logger.warning(f"尝试更新不存在的属性 {key} for {self.model_class.__name__}")
            # 不需要 commit/flush
            return entity
        return None

    def delete(self, session: Session, entity_id: str) -> bool:
        """通过ID删除任务 (覆盖或实现基类方法)"""
        entity = self.get_by_id(session, entity_id)
        if entity:
            session.delete(entity)
            # 不需要 commit/flush
            return True
        return False

    def get_all(self, session: Session, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Task]:
        """获取所有任务 (覆盖或实现基类方法)"""
        query = session.query(self.model_class)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_by_id_with_comments(self, session: Session, task_id: str) -> Optional[Task]:
        """获取任务及其所有评论"""
        return session.query(Task).options(joinedload(Task.comments)).filter(Task.id == task_id).first()

    def search_tasks(
        self,
        session: Session,
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
        query = session.query(Task)

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

        results = query.all()
        return results

    def link_to_roadmap(self, session: Session, task_id: str, roadmap_item_id: Optional[str]) -> Optional[Task]:
        """关联或取消关联任务到 Roadmap Item

        在简化方案中，我们将roadmap_item_id映射到story_id
        """
        logger.info(f"将任务 {task_id} 关联到路线图项 {roadmap_item_id}，映射到story_id")
        return self.update_task(session, task_id, {"story_id": roadmap_item_id})

    def link_to_workflow_stage(self, session: Session, task_id: str, workflow_stage_instance_id: Optional[str]) -> Optional[Task]:
        """关联或取消关联任务到 Workflow Stage Instance"""
        # 检查Task模型是否有workflow_stage_instance_id属性
        if hasattr(Task, "workflow_stage_instance_id"):
            return self.update_task(session, task_id, {"workflow_stage_instance_id": workflow_stage_instance_id})
        else:
            logger.warning("Task模型没有workflow_stage_instance_id属性，无法关联到工作流阶段")
            # 返回未修改的任务
            return self.get_by_id(session, task_id)

    def link_to_github_issue(self, session: Session, task_id: str, issue_number: Optional[int]) -> Optional[Task]:
        """关联或取消关联任务到 GitHub Issue"""
        # 检查Task模型是否有github_issue_number属性
        if hasattr(Task, "github_issue_number"):
            return self.update_task(session, task_id, {"github_issue_number": issue_number})
        else:
            logger.warning("Task模型没有github_issue_number属性，无法关联到GitHub Issue")
            # 返回未修改的任务
            return self.get_by_id(session, task_id)

    def add_linked_pr(self, session: Session, task_id: str, repo: str, pr_number: int) -> Optional[Task]:
        """添加关联的 Pull Request"""
        task = self.get_by_id(session, task_id)
        if not task:
            return None
        linked_prs = task.linked_prs or []
        new_pr = {"repo": repo, "pr_number": pr_number}
        if new_pr not in linked_prs:
            linked_prs.append(new_pr)
            return self.update_task(session, task_id, {"linked_prs": linked_prs})
        return task

    def remove_linked_pr(self, session: Session, task_id: str, repo: str, pr_number: int) -> Optional[Task]:
        """移除关联的 Pull Request"""
        task = self.get_by_id(session, task_id)
        if not task or not task.linked_prs:
            return task
        linked_prs = task.linked_prs
        pr_to_remove = {"repo": repo, "pr_number": pr_number}
        if pr_to_remove in linked_prs:
            linked_prs.remove(pr_to_remove)
            return self.update_task(session, task_id, {"linked_prs": linked_prs})
        return task

    def add_linked_commit(self, session: Session, task_id: str, repo: str, sha: str) -> Optional[Task]:
        """添加关联的 Commit"""
        task = self.get_by_id(session, task_id)
        if not task:
            return None
        linked_commits = task.linked_commits or []
        new_commit = {"repo": repo, "sha": sha}
        if new_commit not in linked_commits:
            linked_commits.append(new_commit)
            return self.update_task(session, task_id, {"linked_commits": linked_commits})
        return task

    def remove_linked_commit(self, session: Session, task_id: str, repo: str, sha: str) -> Optional[Task]:
        """移除关联的 Commit"""
        task = self.get_by_id(session, task_id)
        if not task or not task.linked_commits:
            return task
        linked_commits = task.linked_commits
        commit_to_remove = {"repo": repo, "sha": sha}
        if commit_to_remove in linked_commits:
            linked_commits.remove(commit_to_remove)
            return self.update_task(session, task_id, {"linked_commits": linked_commits})
        return task

    def get_by_story_id(self, session: Session, story_id: str) -> List[Task]:
        """根据故事ID获取任务列表

        Args:
            story_id: 故事ID

        Returns:
            List[Task]: 任务列表
        """
        return session.query(Task).filter(Task.story_id == story_id).all()

    def get_by_roadmap_id(self, session: Session, roadmap_id: str) -> List[Task]:
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
                session.query(Task)
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

    def add_memory_reference(self, session: Session, task_id: str, permalink: str, title: str, added_at: Optional[str] = None) -> Optional[Task]:
        """添加Memory引用到任务

        Args:
            task_id: 任务ID
            permalink: Memory永久链接
            title: 文档标题
            added_at: 添加时间（可选，默认为当前时间）

        Returns:
            更新后的任务，如果失败则返回None
        """
        logger.info(f"开始添加Memory引用: {permalink} 到任务 {task_id}")

        # 参数验证
        if not task_id:
            logger.error("添加Memory引用失败：任务ID不能为空")
            return None

        if not permalink:
            logger.error("添加Memory引用失败：Memory永久链接不能为空")
            return None

        if not title:
            logger.warning("Memory引用标题为空，使用默认标题")
            title = "未命名引用文档"

        # 获取任务
        try:
            task = self.get_by_id(session, task_id)
            if not task:
                logger.error(f"添加Memory引用失败：未找到任务 {task_id}")
                return None
        except Exception as e:
            logger.error(f"获取任务 {task_id} 失败: {e}", exc_info=True)
            return None

        # 准备引用信息
        if not added_at:
            added_at = datetime.utcnow().isoformat()

        reference = {"permalink": permalink, "title": title, "added_at": added_at}

        # 获取现有引用，确保是列表类型
        try:
            memory_references = task.memory_references
            # 确保memory_references是列表类型
            if memory_references is None:
                memory_references = []
            elif not isinstance(memory_references, list):
                logger.warning(f"任务 {task_id} 的memory_references不是列表类型，将重置为空列表")
                memory_references = []
        except Exception as e:
            logger.error(f"获取任务 {task_id} 的memory_references时出错: {e}", exc_info=True)
            memory_references = []

        logger.info(f"当前任务 {task_id} 有 {len(memory_references)} 个Memory引用")

        # 检查是否已存在相同的引用
        for ref in memory_references:
            if isinstance(ref, dict) and ref.get("permalink") == permalink:
                logger.info(f"Memory引用 {permalink} 已存在于任务 {task_id}")
                return task

        # 添加新引用
        memory_references.append(reference)
        logger.info(f"添加新引用到任务 {task_id}: {permalink}")

        # 更新任务
        try:
            updated_task = self.update_task(session, task_id, {"memory_references": memory_references})
            if updated_task:
                logger.info(f"成功更新任务 {task_id}，添加Memory引用 {permalink}")
                return updated_task
            else:
                logger.error(f"更新任务 {task_id} 添加Memory引用失败")
                return None
        except ValueError as ve:
            logger.error(f"更新任务 {task_id} 添加Memory引用时数据验证失败: {ve}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"更新任务 {task_id} 添加Memory引用时出错: {e}", exc_info=True)
            return None

    def remove_memory_reference(self, session: Session, task_id: str, permalink: str) -> Optional[Task]:
        """从任务中移除Memory引用

        Args:
            task_id: 任务ID
            permalink: 要移除的Memory永久链接

        Returns:
            更新后的任务，如果失败则返回None
        """
        # 获取任务
        task = self.get_by_id(session, task_id)
        if not task:
            logger.warning(f"移除Memory引用失败：未找到任务 {task_id}")
            return None

        # 获取现有引用
        memory_references = task.memory_references or []

        # 查找并移除引用
        new_references = [ref for ref in memory_references if ref.get("permalink") != permalink]

        # 如果没有变化，直接返回
        if len(new_references) == len(memory_references):
            logger.info(f"未找到Memory引用 {permalink}，无需移除")
            return task

        # 更新任务
        return self.update_task(session, task_id, {"memory_references": new_references})

    def get_memory_references(self, session: Session, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的所有Memory引用

        Args:
            task_id: 任务ID

        Returns:
            引用列表，如果任务不存在或没有引用则返回空列表
        """
        task = self.get_by_id(session, task_id)
        if not task:
            logger.warning(f"获取Memory引用失败：未找到任务 {task_id}")
            return []

        return task.memory_references or []


class TaskCommentRepository(Repository[TaskComment]):
    """任务评论仓库"""

    def __init__(self):
        super().__init__(None, TaskComment)

    def get_comments_for_task(self, session: Session, task_id: str, limit: Optional[int] = None, offset: Optional[int] = None) -> List[TaskComment]:
        """获取任务的所有评论"""
        query = session.query(TaskComment).filter(TaskComment.task_id == task_id).order_by(TaskComment.created_at)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all()

    def add_comment(self, session: Session, task_id: str, content: str, author: Optional[str] = None) -> TaskComment:
        """添加评论到任务

        Args:
            task_id: 任务ID
            content: 评论内容
            author: 评论作者

        Returns:
            新创建的评论对象
        """
        # 使用通用ID生成方法，由于没有专门为评论设置EntityType，使用GENERIC
        comment_id = IdGenerator.generate_id(EntityType.GENERIC, "comment")

        # 准备评论数据
        now = datetime.utcnow()
        comment_data = {"id": comment_id, "task_id": task_id, "content": content, "author": author or "system", "created_at": now}

        # 创建评论
        return super().create(comment_data)
