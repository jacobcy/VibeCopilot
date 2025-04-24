"""
里程碑导入器模块

提供里程碑导入功能。
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from .base_importer import BaseImporter
from .task_importer import TaskImporter

logger = logging.getLogger(__name__)


class MilestoneImporter(BaseImporter):
    """里程碑导入器，提供里程碑导入功能"""

    def import_milestones(self, yaml_data: Dict[str, Any], roadmap_id: str, import_stats: Dict[str, Dict[str, int]]) -> None:
        """
        导入里程碑数据

        Args:
            yaml_data: YAML数据
            roadmap_id: 路线图ID
            import_stats: 导入统计信息
        """
        if "milestones" not in yaml_data or not isinstance(yaml_data["milestones"], list):
            return

        task_importer = TaskImporter(self.service, self.verbose, self.stop_on_error)

        for milestone_data in yaml_data["milestones"]:
            try:
                milestone_title = milestone_data.get("title", "Unnamed Milestone")

                # 处理里程碑导入
                milestone_id = self._process_milestone(milestone_data, roadmap_id, milestone_title, import_stats)
                if not milestone_id:
                    continue

                # 导入里程碑下的任务
                if "tasks" in milestone_data and isinstance(milestone_data["tasks"], list):
                    task_importer.import_tasks(milestone_data["tasks"], milestone_id, roadmap_id, import_stats)

            except Exception as e:
                error_msg = f"导入里程碑失败: {milestone_data.get('title', 'Unknown')}"
                self.handle_import_error(error_msg, e, import_stats, "milestones")

    def _process_milestone(
        self, milestone_data: Dict[str, Any], roadmap_id: str, milestone_title: str, import_stats: Dict[str, Dict[str, int]]
    ) -> Optional[str]:
        """处理单个里程碑的导入或更新"""
        try:
            # 查找是否已存在同名里程碑
            existing_milestone = self._find_existing_milestone(roadmap_id, milestone_title)

            if existing_milestone:
                # 更新现有里程碑
                return self._update_milestone(existing_milestone, milestone_data, milestone_title)
            else:
                # 创建新里程碑
                return self._create_milestone(milestone_data, roadmap_id, milestone_title, import_stats)

        except Exception as e:
            self.handle_import_error(f"处理里程碑失败: {milestone_title}", e, import_stats, "milestones")
            return None

    def _find_existing_milestone(self, roadmap_id: str, milestone_title: str) -> Optional[Any]:
        """查找是否已存在同名里程碑"""
        existing_milestones = self.service.milestone_repo.get_by_roadmap_id(roadmap_id)

        for milestone in existing_milestones:
            if milestone.title == milestone_title:
                return milestone

        return None

    def _update_milestone(self, existing_milestone: Any, milestone_data: Dict[str, Any], milestone_title: str) -> str:
        """更新现有里程碑"""
        milestone_id = existing_milestone.id

        if self.verbose:
            logger.debug(f"里程碑已存在，进行更新: {milestone_title} (ID: {milestone_id})")

        # 更新现有里程碑
        update_data = {
            "title": milestone_title,
            "description": milestone_data.get("description", ""),
            "status": milestone_data.get("status", "planned"),
            "updated_at": str(self.service.get_now()),
        }

        self.service.milestone_repo.update(milestone_id, update_data)

        if self.verbose:
            self.log_info(f"更新里程碑: {milestone_title} (ID: {milestone_id})")
        else:
            self.log_success(f"更新里程碑: {milestone_title}")

        return milestone_id

    def _create_milestone(
        self, milestone_data: Dict[str, Any], roadmap_id: str, milestone_title: str, import_stats: Dict[str, Dict[str, int]]
    ) -> Optional[str]:
        """创建新里程碑"""
        # 创建新里程碑，使用UUID生成ID
        milestone_id = f"milestone-{uuid.uuid4()}"

        # 准备里程碑数据
        milestone_obj = {
            "id": milestone_id,
            "title": milestone_title,
            "description": milestone_data.get("description", ""),
            "status": milestone_data.get("status", "planned"),
            "roadmap_id": roadmap_id,
            "created_at": str(self.service.get_now()),
            "updated_at": str(self.service.get_now()),
        }

        try:
            # 创建新里程碑
            self.service.milestone_repo.create(milestone_obj)

            if self.verbose:
                self.log_info(f"导入里程碑: {milestone_title} (ID: {milestone_id})")
            else:
                self.log_success(f"导入里程碑: {milestone_title}")

            import_stats["milestones"]["success"] += 1
            return milestone_id

        except Exception as create_error:
            # 处理创建过程中的错误
            error_msg = f"创建里程碑失败: {milestone_title}: {str(create_error)}"
            self.handle_import_error(error_msg, create_error, import_stats, "milestones")
            return None
