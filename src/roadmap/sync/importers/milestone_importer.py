"""
里程碑导入器模块

提供里程碑导入功能。
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repositories.roadmap_repository import MilestoneRepository
from src.db.session_manager import session_scope

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
        milestone_id: Optional[str] = None
        try:
            # 使用 session_scope
            with session_scope() as session:
                # 查找是否已存在同名里程碑 (使用新方法)
                existing_milestone = self.service.milestone_repo.get_by_title_and_roadmap_id(session, milestone_title, roadmap_id)

                if existing_milestone:
                    # 更新现有里程碑 (传入 session)
                    milestone_id = self._update_milestone(session, existing_milestone, milestone_data, milestone_title)
                else:
                    # 创建新里程碑 (传入 session)
                    milestone_id = self._create_milestone(session, milestone_data, roadmap_id, milestone_title, import_stats)

            # Update stats based on whether milestone_id was obtained
            if milestone_id:
                # Success count is handled within _create_milestone
                if existing_milestone:  # If it was an update, count success here
                    import_stats["milestones"]["success"] += 1

            return milestone_id

        except Exception as e:
            self.handle_import_error(f"处理里程碑失败: {milestone_title}", e, import_stats, "milestones")
            return None

    def _update_milestone(self, session: Session, existing_milestone: Any, milestone_data: Dict[str, Any], milestone_title: str) -> Optional[str]:
        """更新现有里程碑 (需要 session 参数)"""
        milestone_id = existing_milestone.id
        updated_milestone: Optional[Any] = None
        try:
            if self.verbose:
                logger.debug(f"里程碑已存在，进行更新: {milestone_title} (ID: {milestone_id})")

            # 更新现有里程碑数据准备
            update_data = {
                # title 不更新
                "description": milestone_data.get("description", existing_milestone.description),
                "status": milestone_data.get("status", existing_milestone.status),
                "updated_at": str(self.service.get_now()),
            }

            # 在传入的 session 上执行更新
            updated_milestone = self.service.milestone_repo.update(session, milestone_id, update_data)

            if not updated_milestone:
                self.log_warning(f"尝试更新里程碑 {milestone_title} (ID: {milestone_id}) 但仓库未返回更新对象。")
                return milestone_id  # Return ID anyway

            if self.verbose:
                self.log_info(f"更新里程碑: {milestone_title} (ID: {milestone_id})")

            return milestone_id
        except Exception as e:
            self.log_error(f"更新里程碑 {milestone_title} 时出错: {e}", show_traceback=True)
            return None  # Signal failure

    def _create_milestone(
        self, session: Session, milestone_data: Dict[str, Any], roadmap_id: str, milestone_title: str, import_stats: Dict[str, Dict[str, int]]
    ) -> Optional[str]:
        """创建新里程碑 (需要 session 参数)"""
        created_milestone: Optional[Any] = None
        try:
            # 准备里程碑数据 (移除 id, 让 repo 处理)
            create_data = {
                "title": milestone_title,
                "description": milestone_data.get("description", ""),
                "status": milestone_data.get("status", "planned"),
                "roadmap_id": roadmap_id,
                # Timestamps handled by repo create
                # "created_at": str(self.service.get_now()),
                # "updated_at": str(self.service.get_now()),
            }

            # 在传入的 session 上执行创建
            created_milestone = self.service.milestone_repo.create(session, **create_data)

            if not created_milestone or not hasattr(created_milestone, "id"):
                raise ValueError("创建 Milestone 后未能获取有效对象或 ID。")

            milestone_id = created_milestone.id

            if self.verbose:
                self.log_info(f"导入里程碑: {milestone_title} (ID: {milestone_id})")
            else:
                self.log_success(f"导入里程碑: {milestone_title}")

            import_stats["milestones"]["success"] += 1  # Increment here on successful create
            return milestone_id

        except Exception as create_error:
            # Failure count handled by handle_import_error in the calling method
            error_msg = f"创建里程碑失败: {milestone_title}: {str(create_error)}"
            self.handle_import_error(error_msg, create_error, import_stats, "milestones")
            raise create_error  # Re-raise
