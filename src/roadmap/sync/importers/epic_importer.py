"""
史诗导入器模块

提供史诗导入功能。
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from ..utils import colorize
from .base_importer import BaseImporter
from .story_importer import StoryImporter

logger = logging.getLogger(__name__)


class EpicImporter(BaseImporter):
    """史诗导入器，提供史诗导入功能"""

    def import_epics(self, yaml_data: Dict[str, Any], roadmap_id: str, import_stats: Dict[str, Dict[str, int]]) -> None:
        """
        导入史诗数据

        Args:
            yaml_data: YAML数据
            roadmap_id: 路线图ID
            import_stats: 导入统计信息
        """
        if "epics" not in yaml_data or not isinstance(yaml_data["epics"], list):
            return

        story_importer = StoryImporter(self.service, self.verbose, self.stop_on_error)

        for epic_data in yaml_data["epics"]:
            try:
                epic_title = epic_data.get("title", "Unnamed Epic")

                # 处理史诗导入
                epic_id = self._process_epic(epic_data, roadmap_id, epic_title, import_stats)
                if not epic_id:
                    continue

                # 导入史诗下的故事
                if "stories" in epic_data and isinstance(epic_data["stories"], list):
                    story_importer.import_stories(epic_data["stories"], epic_id, import_stats)

            except Exception as e:
                error_msg = f"导入史诗失败: {epic_data.get('title', 'Unknown')}"
                self.handle_import_error(error_msg, e, import_stats, "epics")

    def _process_epic(self, epic_data: Dict[str, Any], roadmap_id: str, epic_title: str, import_stats: Dict[str, Dict[str, int]]) -> Optional[str]:
        """处理单个史诗的导入或更新"""
        try:
            # 查找是否已存在同名史诗
            existing_epic = self._find_existing_epic(roadmap_id, epic_title)

            if existing_epic:
                # 更新现有史诗
                return self._update_epic(existing_epic, epic_data, epic_title)
            else:
                # 创建新史诗
                return self._create_epic(epic_data, roadmap_id, epic_title, import_stats)

        except Exception as e:
            self.handle_import_error(f"处理史诗失败: {epic_title}", e, import_stats, "epics")
            return None

    def _find_existing_epic(self, roadmap_id: str, epic_title: str) -> Optional[Any]:
        """查找是否已存在同名史诗"""
        existing_epics = self.service.epic_repo.get_by_roadmap_id(roadmap_id)

        for epic in existing_epics:
            if epic.title == epic_title:
                return epic

        return None

    def _update_epic(self, existing_epic: Any, epic_data: Dict[str, Any], epic_title: str) -> str:
        """更新现有史诗"""
        epic_id = existing_epic.id

        if self.verbose:
            print(colorize(f"史诗已存在，进行更新: {epic_title} (ID: {epic_id})", "cyan"))

        # 更新现有史诗
        update_data = {
            "title": epic_title,
            "description": epic_data.get("description", ""),
            "status": epic_data.get("status", "planned"),
            "updated_at": str(self.service.get_now()),
        }

        self.service.epic_repo.update(epic_id, update_data)

        if self.verbose:
            self.log_info(f"更新史诗: {epic_title} (ID: {epic_id})")
        else:
            self.log_success(f"更新史诗: {epic_title}")

        return epic_id

    def _create_epic(self, epic_data: Dict[str, Any], roadmap_id: str, epic_title: str, import_stats: Dict[str, Dict[str, int]]) -> Optional[str]:
        """创建新史诗"""
        # 创建新史诗，使用UUID生成ID
        epic_id = f"epic-{uuid.uuid4()}"

        # 准备史诗数据
        epic_obj = {
            "id": epic_id,
            "title": epic_title,
            "description": epic_data.get("description", ""),
            "status": epic_data.get("status", "planned"),
            "roadmap_id": roadmap_id,
            "created_at": str(self.service.get_now()),
            "updated_at": str(self.service.get_now()),
        }

        try:
            # 创建新史诗
            self.service.epic_repo.create(epic_obj)

            if self.verbose:
                self.log_info(f"导入史诗: {epic_title} (ID: {epic_id})")
            else:
                self.log_success(f"导入史诗: {epic_title}")

            import_stats["epics"]["success"] += 1
            return epic_id

        except Exception as create_error:
            # 处理创建过程中的错误
            error_msg = f"创建史诗失败: {epic_title}: {str(create_error)}"
            self.handle_import_error(error_msg, create_error, import_stats, "epics")
            return None
