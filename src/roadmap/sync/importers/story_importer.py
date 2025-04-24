"""
故事导入器模块

提供故事导入功能。
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from .base_importer import BaseImporter
from .task_importer import TaskImporter

logger = logging.getLogger(__name__)


class StoryImporter(BaseImporter):
    """故事导入器，提供故事导入功能"""

    def import_stories(self, stories_data: List[Dict[str, Any]], epic_id: str, import_stats: Dict[str, Dict[str, int]]) -> None:
        """
        导入故事数据

        Args:
            stories_data: 故事数据列表
            epic_id: 史诗ID
            import_stats: 导入统计信息
        """
        # 初始化任务导入器
        task_importer = TaskImporter(self.service, self.verbose, self.stop_on_error)

        for story_data in stories_data:
            try:
                story_title = story_data.get("title", "Unnamed Story")

                # 处理故事导入
                story_id = self._process_story(story_data, epic_id, story_title, import_stats)

                # 如果故事创建/更新成功并且包含任务，导入任务
                if story_id and "tasks" in story_data and isinstance(story_data["tasks"], list):
                    logger.info(f"为故事 '{story_title}' 导入 {len(story_data['tasks'])} 个任务")
                    if self.verbose:
                        logger.debug(f"为故事 '{story_title}' 导入 {len(story_data['tasks'])} 个任务")

                    # 使用任务导入器导入任务，story_id作为任务的关联ID，不需要milestone_id
                    task_importer.import_tasks(
                        story_data["tasks"], None, None, import_stats, story_id  # 无需milestone_id  # 无需roadmap_id，使用story_id  # 传递story_id
                    )

            except Exception as e:
                error_msg = f"导入故事失败: {story_data.get('title', 'Unknown')}"
                self.handle_import_error(error_msg, e, import_stats, "stories")

    def _process_story(self, story_data: Dict[str, Any], epic_id: str, story_title: str, import_stats: Dict[str, Dict[str, int]]) -> Optional[str]:
        """处理单个故事的导入或更新"""
        try:
            # 查找是否已存在同名故事
            existing_story = self._find_existing_story(epic_id, story_title)

            if existing_story:
                # 更新现有故事
                story_id = self._update_story(existing_story, story_data, story_title)
            else:
                # 创建新故事
                story_id = self._create_story(story_data, epic_id, story_title, import_stats)

            if story_id:
                import_stats["stories"]["success"] += 1

            return story_id

        except Exception as e:
            self.handle_import_error(f"处理故事失败: {story_title}", e, import_stats, "stories")
            return None

    def _find_existing_story(self, epic_id: str, story_title: str) -> Optional[Any]:
        """查找是否已存在同名故事"""
        existing_stories = self.service.story_repo.get_by_epic_id(epic_id)

        for story in existing_stories:
            if story.title == story_title:
                return story

        return None

    def _update_story(self, existing_story: Any, story_data: Dict[str, Any], story_title: str) -> str:
        """更新现有故事"""
        story_id = existing_story.id

        if self.verbose:
            logger.debug(f"故事已存在，进行更新: {story_title} (ID: {story_id})")

        # 更新现有故事
        update_data = {
            "title": story_title,
            "description": story_data.get("description", ""),
            "status": story_data.get("status", "todo"),
            "priority": story_data.get("priority", "medium"),
            "updated_at": str(self.service.get_now()),
        }

        self.service.story_repo.update(story_id, update_data)

        if self.verbose:
            self.log_info(f"更新故事: {story_title} (ID: {story_id})")
        else:
            self.log_success(f"更新故事: {story_title}")

        return story_id

    def _create_story(self, story_data: Dict[str, Any], epic_id: str, story_title: str, import_stats: Dict[str, Dict[str, int]]) -> Optional[str]:
        """创建新故事"""
        # 创建新故事，使用UUID生成ID
        story_id = f"story-{uuid.uuid4()}"

        # 准备故事数据
        story_obj = {
            "id": story_id,
            "title": story_title,
            "description": story_data.get("description", ""),
            "status": story_data.get("status", "todo"),
            "priority": story_data.get("priority", "medium"),
            "epic_id": epic_id,
            "created_at": str(self.service.get_now()),
            "updated_at": str(self.service.get_now()),
        }

        try:
            # 创建新故事
            self.service.story_repo.create(story_obj)

            if self.verbose:
                self.log_info(f"导入故事: {story_title} (ID: {story_id})")
            else:
                self.log_success(f"导入故事: {story_title}")

            return story_id

        except Exception as create_error:
            # 处理创建过程中的错误
            error_msg = f"创建故事失败: {story_title}: {str(create_error)}"
            self.handle_import_error(error_msg, create_error, import_stats, "stories")
            return None
