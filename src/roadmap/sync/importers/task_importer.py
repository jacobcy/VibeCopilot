"""
任务导入器模块

提供任务导入功能。
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from ..utils import colorize
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
            print(colorize(f"开始导入 {len(tasks_data)} 个任务到{parent_type} ID: {parent_id}", "cyan"))

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
        try:
            # 查找是否已存在同名任务，优先按故事ID查找
            existing_task = None
            if story_id:
                existing_task = self._find_existing_task_by_story(story_id, task_title)
            elif milestone_id:
                existing_task = self._find_existing_task(milestone_id, task_title)

            if existing_task:
                # 更新现有任务
                task_id = self._update_task(existing_task, task_data, task_title)
            else:
                # 创建新任务
                task_id = self._create_task(task_data, milestone_id, roadmap_id, task_title, import_stats, story_id)

            if task_id:
                import_stats["tasks"]["success"] += 1

            return task_id

        except Exception as e:
            self.handle_import_error(f"处理任务失败: {task_title}", e, import_stats, "tasks")
            return None

    def _find_existing_task(self, milestone_id: Optional[str], task_title: str) -> Optional[Any]:
        """查找是否已存在同名任务（按里程碑ID）"""
        # 使用search_tasks通过milestone_id查询任务
        if not milestone_id:
            return None

        existing_tasks = self.service.task_repo.search_tasks(roadmap_item_id=milestone_id)

        for task in existing_tasks:
            if task.title == task_title:
                return task

        return None

    def _find_existing_task_by_story(self, story_id: str, task_title: str) -> Optional[Any]:
        """查找是否已存在同名任务（按故事ID）"""
        if not story_id:
            return None

        try:
            # 使用search_tasks通过story_id查询任务
            existing_tasks = self.service.task_repo.search_tasks(story_id=story_id)

            for task in existing_tasks:
                if task.title == task_title:
                    return task
        except Exception as e:
            logger.warning(f"按故事ID查找任务失败: {e}")
            # 如果search_tasks不支持story_id，则返回None

        return None

    def _update_task(self, existing_task: Any, task_data: Dict[str, Any], task_title: str) -> str:
        """更新现有任务"""
        task_id = existing_task.id

        if self.verbose:
            print(colorize(f"任务已存在，进行更新: {task_title} (ID: {task_id})", "cyan"))

        # 更新现有任务
        update_data = {
            "title": task_title,
            "description": task_data.get("description", ""),
            "status": task_data.get("status", "todo"),
            "priority": task_data.get("priority", "medium"),
            "updated_at": str(self.service.get_now()),
        }

        self.service.task_repo.update(task_id, update_data)

        if self.verbose:
            self.log_info(f"更新任务: {task_title} (ID: {task_id})")
        else:
            self.log_success(f"更新任务: {task_title}")

        return task_id

    def _create_task(
        self,
        task_data: Dict[str, Any],
        milestone_id: Optional[str],
        roadmap_id: Optional[str],
        task_title: str,
        import_stats: Dict[str, Dict[str, int]],
        story_id: Optional[str] = None,
    ) -> Optional[str]:
        """创建新任务"""
        # 创建新任务，使用UUID生成ID
        task_id = f"task-{uuid.uuid4()}"

        # 准备任务数据
        task_obj = {
            "id": task_id,
            "title": task_title,
            "description": task_data.get("description", ""),
            "status": task_data.get("status", "todo"),
            "priority": task_data.get("priority", "medium"),
            "created_at": str(self.service.get_now()),
            "updated_at": str(self.service.get_now()),
        }

        # 设置关联ID，优先级: story_id > milestone_id > roadmap_id
        if story_id:
            task_obj["story_id"] = story_id
            # 记录日志
            logger.info(f"任务 '{task_title}' 关联到故事 ID: {story_id}")
        elif milestone_id:
            task_obj["milestone_id"] = milestone_id
            task_obj["roadmap_item_id"] = milestone_id  # 兼容旧字段
            logger.info(f"任务 '{task_title}' 关联到里程碑 ID: {milestone_id}")

        # 无论关联到哪个父对象，都设置roadmap_id
        if roadmap_id:
            task_obj["roadmap_id"] = roadmap_id

        try:
            # 创建新任务
            self.service.task_repo.create(task_obj)

            if self.verbose:
                parent_info = f"[关联到:{story_id or milestone_id or roadmap_id}]" if story_id or milestone_id or roadmap_id else ""
                self.log_info(f"导入任务: {task_title} (ID: {task_id}) {parent_info}")
            else:
                self.log_success(f"导入任务: {task_title}")

            return task_id

        except Exception as create_error:
            # 处理创建过程中的错误
            error_msg = f"创建任务失败: {task_title}: {str(create_error)}"
            self.handle_import_error(error_msg, create_error, import_stats, "tasks")
            return None
