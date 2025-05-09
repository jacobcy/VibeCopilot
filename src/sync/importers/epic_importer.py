"""
史诗导入器模块

提供史诗导入功能。
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.repositories.roadmap_repository import EpicRepository
from src.db.session_manager import session_scope

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
            # 使用 session_scope
            with session_scope() as session:
                # 查找是否已存在同名史诗 (使用新方法)
                existing_epic = self.service.epic_repo.get_by_title_and_roadmap_id(session, epic_title, roadmap_id)

                if existing_epic:
                    # 更新现有史诗 (传入 session)
                    return self._update_epic(session, existing_epic, epic_data, epic_title)
                else:
                    # 创建新史诗 (传入 session)
                    return self._create_epic(session, epic_data, roadmap_id, epic_title, import_stats)

        except Exception as e:
            self.handle_import_error(f"处理史诗失败: {epic_title}", e, import_stats, "epics")
            return None

    def _update_epic(self, session: Session, existing_epic: Any, epic_data: Dict[str, Any], epic_title: str) -> str:
        """更新现有史诗 (需要 session 参数)"""
        epic_id = existing_epic.id

        if self.verbose:
            logger.info(f"史诗已存在，进行更新: {epic_title} (ID: {epic_id})")

        # 更新现有史诗数据准备
        update_data = {
            # title 不在此处更新，因为是基于 title 查找的
            "description": epic_data.get("description", existing_epic.description),  # 保留旧描述如果未提供
            "status": epic_data.get("status", existing_epic.status),  # 保留旧状态如果未提供
            "updated_at": str(self.service.get_now()),
        }

        # 在传入的 session 上执行更新
        updated_epic = self.service.epic_repo.update(session, epic_id, update_data)

        if not updated_epic:
            # 更新失败或未找到（理论上应该找到，因为是基于查找结果调用的）
            self.log_warning(f"尝试更新史诗 '{epic_title}' (ID: {epic_id}) 但仓库未返回更新对象。")
            # 可以选择抛出异常或仅记录警告并继续
            return epic_id  # 仍然返回 ID，但标记可能存在问题

        if self.verbose:
            self.log_info(f"更新史诗: {epic_title} (ID: {epic_id})")
        else:
            self.log_success(f"更新史诗: {epic_title}")

        return epic_id

    def _create_epic(
        self, session: Session, epic_data: Dict[str, Any], roadmap_id: str, epic_title: str, import_stats: Dict[str, Dict[str, int]]
    ) -> Optional[str]:
        """创建新史诗 (需要 session 参数)"""
        created_epic: Optional[Any] = None
        try:
            # 准备史诗数据 (移除 id，让 repo 生成)
            create_data = {
                # "id": epic_id,
                "title": epic_title,
                "description": epic_data.get("description", ""),
                "status": epic_data.get("status", "planned"),
                "roadmap_id": roadmap_id,
                "created_at": str(self.service.get_now()),
                "updated_at": str(self.service.get_now()),
            }

            # 在传入的 session 上执行创建
            created_epic = self.service.epic_repo.create(session, **create_data)

            if not created_epic or not hasattr(created_epic, "id"):
                raise ValueError("创建 Epic 后未能获取有效对象或 ID。")

            epic_id = created_epic.id

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
