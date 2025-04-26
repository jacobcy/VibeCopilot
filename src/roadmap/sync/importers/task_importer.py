"""
任务导入器模块

提供任务导入功能。
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.db.repositories.task_repository import TaskRepository
from src.db.session_manager import session_scope

from .base_importer import BaseImporter

logger = logging.getLogger(__name__)


class TaskImporter(BaseImporter):
    """任务导入器，提供任务导入功能"""

    def import_tasks(
        self,
        tasks_data: List[Dict[str, Any]],
        milestone_id: Optional[str] = None,
        roadmap_id: Optional[str] = None,
        import_stats: Optional[Dict[str, Dict[str, int]]] = None,
        story_id: Optional[str] = None,
    ) -> None:
        """
        导入任务数据

        Args:
            tasks_data: 任务数据列表
            milestone_id: 里程碑ID (可选)
            roadmap_id: 路线图ID (可选)
            import_stats: 导入统计信息 (可选)
            story_id: 故事ID (可选)
        """
        # 确保import_stats存在
        if import_stats is None:
            import_stats = {"tasks": {"success": 0, "failed": 0}}

        if self.verbose:
            parent_type = "故事" if story_id else "里程碑" if milestone_id else "路线图"
            parent_id = story_id or milestone_id or roadmap_id
            logger.debug(f"开始导入 {len(tasks_data)} 个任务到{parent_type} ID: {parent_id}")

        logger.info(f"导入 {len(tasks_data)} 个任务，story_id={story_id}, milestone_id={milestone_id}, roadmap_id={roadmap_id}")

        for task_data in tasks_data:
            try:
                task_title = task_data.get("title", "Unnamed Task")

                # 处理任务导入
                self._process_task(task_data, milestone_id, roadmap_id, task_title, import_stats, story_id)

            except Exception as e:
                error_msg = f"导入任务失败: {task_data.get('title', 'Unknown')}"
                self.handle_import_error(error_msg, e, import_stats, "tasks")

    def _process_task(
        self,
        task_data: Dict[str, Any],
        milestone_id: Optional[str],
        roadmap_id: Optional[str],
        task_title: str,
        import_stats: Dict[str, Dict[str, int]],
        story_id: Optional[str] = None,
    ) -> Optional[str]:
        """处理单个任务的导入或更新"""
        task_id: Optional[str] = None
        try:
            # --- 使用 session_scope ---
            with session_scope() as session:
                existing_task = None
                # 优先按故事ID查找
                if story_id:
                    existing_task = self.service.task_repo.get_by_title_and_story_id(session, task_title, story_id)
                # Task 模型没有 milestone_id，所以不能按 milestone 查找同名任务
                # elif milestone_id:
                #     # Add get_by_title_and_milestone_id to TaskRepository if needed
                #     # existing_task = self.service.task_repo.get_by_title_and_milestone_id(session, task_title, milestone_id)
                #     logger.warning(f"Task model does not support milestone_id link. Cannot find existing task '{task_title}' by milestone.")

                if existing_task:
                    # 更新现有任务 (传入 session)
                    task_id = self._update_task(session, existing_task, task_data, task_title)
                else:
                    # 创建新任务 (传入 session)
                    # 确保 story_id 存在，否则无法创建关联的任务
                    if not story_id:
                        logger.warning(f"无法创建任务 '{task_title}'，因为它没有关联的 Story ID 且模型不支持直接关联 Milestone。")
                        # Increment failure count?
                        import_stats["tasks"]["failed"] += 1
                        return None  # Skip creation

                    task_id = self._create_task(session, task_data, roadmap_id, task_title, import_stats, story_id)
            # ------------------------

            # Update stats based on whether task_id was obtained
            if task_id:
                # Check if the operation actually incremented failure inside create/update
                # Assuming success if we get an ID back and no exception was re-raised
                # Success count is handled within _create_task for now
                if existing_task:  # If it was an update, count success here
                    import_stats["tasks"]["success"] += 1
            # else: # Failure count handled by handle_import_error or logic above
            #     pass

            return task_id

        except Exception as e:
            self.handle_import_error(f"处理任务 '{task_title}' 时出错", e, import_stats, "tasks")
            return None

    def _update_task(self, session: Session, existing_task: Any, task_data: Dict[str, Any], task_title: str) -> Optional[str]:
        """更新现有任务 (需要 session 参数)"""
        task_id = existing_task.id
        updated_task: Optional[Any] = None
        try:
            if self.verbose:
                logger.debug(f"任务 '{task_title}' 已存在，进行更新 (ID: {task_id})")

            # 更新现有任务数据准备
            update_data = {
                # title 不更新
                "description": task_data.get("description", existing_task.description),
                "status": task_data.get("status", existing_task.status),
                "priority": task_data.get("priority", existing_task.priority),
                "assignee": task_data.get("assignee", existing_task.assignee),
                "labels": task_data.get("labels", existing_task.labels),
                "due_date": task_data.get("due_date", existing_task.due_date),
                "updated_at": str(self.service.get_now()),
            }

            # --- 在传入的 session 上执行更新 ---
            # Use update_task which handles specific logic like closed_at
            updated_task = self.service.task_repo.update_task(session, task_id, update_data)
            # -----------------------------------

            if not updated_task:
                self.log_warning(f"尝试更新任务 '{task_title}' (ID: {task_id}) 但仓库未返回更新对象。")
                return task_id  # Return ID even if update seems problematic

            if self.verbose:
                self.log_info(f"更新任务: {task_title} (ID: {task_id})")
            # else:
            #     self.log_success(f"更新任务: {task_title}") # Only log success in create

            return task_id
        except Exception as e:
            self.log_error(f"更新任务 '{task_title}' 时出错: {e}", show_traceback=True)
            return None  # Signal failure

    def _create_task(
        self,
        session: Session,
        task_data: Dict[str, Any],
        roadmap_id: Optional[str],
        task_title: str,
        import_stats: Dict[str, Dict[str, int]],
        story_id: Optional[str] = None,
    ) -> Optional[str]:
        """创建新任务 (需要 session 参数)"""
        created_task: Optional[Any] = None
        try:
            # 准备任务数据 (移除 id，让 repo 处理)
            create_data = {
                "title": task_title,
                "description": task_data.get("description", ""),
                "status": task_data.get("status", "todo"),
                "priority": task_data.get("priority", "medium"),
                "assignee": task_data.get("assignee"),
                "labels": task_data.get("labels"),  # Repo create sets default [] if None
                "due_date": task_data.get("due_date"),
                # --- 关联 ID ---
                "story_id": story_id,  # Directly pass story_id
                # Task model does not have roadmap_id directly
                # "roadmap_id": roadmap_id,
                # ----------------
                # Timestamps are handled by repo create
                # "created_at": str(self.service.get_now()),
                # "updated_at": str(self.service.get_now()),
            }

            # --- 在传入的 session 上执行创建 ---
            created_task = self.service.task_repo.create(session, **create_data)
            # -----------------------------------

            if not created_task or not hasattr(created_task, "id"):
                raise ValueError("创建 Task 后未能获取有效对象或 ID。")

            task_id = created_task.id

            if self.verbose:
                parent_info = f"[关联到 Story:{story_id}]" if story_id else "[无关联父项]"
                self.log_info(f"导入任务: {task_title} (ID: {task_id}) {parent_info}")
            else:
                self.log_success(f"导入任务: {task_title}")

            # Increment success count here for create
            # import_stats["tasks"]["success"] += 1 # Moved out to _process_task
            return task_id

        except Exception as create_error:
            error_msg = f"创建任务 '{task_title}' 失败: {str(create_error)}"
            # self.handle_import_error(error_msg, create_error, import_stats, "tasks") # Called in _process_task
            self.log_error(error_msg, show_traceback=True)
            raise create_error  # Re-raise
            # return None
