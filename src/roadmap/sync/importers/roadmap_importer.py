"""
路线图导入器模块

提供路线图元数据导入功能。
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from src.db.session_manager import session_scope

from .base_importer import BaseImporter

logger = logging.getLogger(__name__)


class RoadmapImporter(BaseImporter):
    """路线图导入器，提供路线图元数据导入功能"""

    def get_or_create_roadmap(self, yaml_data: Dict[str, Any], file_path: Optional[str] = None) -> str:
        """
        从YAML数据中获取或创建路线图，返回路线图ID (在单个Session中完成)

        Args:
            yaml_data: 路线图YAML数据
            file_path: YAML文件路径，用于推断路线图名称

        Returns:
            str: 路线图ID
        """
        # 提取路线图元数据
        roadmap_name, roadmap_description, roadmap_version = self._extract_roadmap_metadata(yaml_data, file_path)

        with session_scope() as session:
            try:
                # 查找现有路线图 (使用当前session)
                roadmap_obj = self.service.roadmap_repo.get_by_name(session, roadmap_name)
                if roadmap_obj:
                    roadmap_id = roadmap_obj.id
                    logger.info(f"找到现有路线图: {roadmap_name}, ID: {roadmap_id}")
                    return roadmap_id

                # 创建新路线图 (使用当前session)
                logger.info(f"创建新路线图: {roadmap_name}")
                roadmap_data = {
                    "title": roadmap_name,
                    "description": roadmap_description,
                    "version": roadmap_version,
                    "status": "active",
                }
                new_roadmap_obj = self.service.roadmap_repo.create(session, **roadmap_data)

                if not new_roadmap_obj or not hasattr(new_roadmap_obj, "id"):
                    self.log_error(f"创建路线图 '{roadmap_name}' 后未能获取有效对象或ID。")
                    raise Exception(f"创建路线图失败: {roadmap_name}")

                roadmap_id = new_roadmap_obj.id
                logger.info(f"创建新路线图成功, ID: {roadmap_id}")
                # Session 提交由 session_scope 处理
                return roadmap_id

            except Exception as e:
                # session_scope 会处理回滚
                self.log_error(f"获取或创建路线图时出错: {e}", show_traceback=True)
                raise Exception(f"获取或创建路线图 '{roadmap_name}' 失败: {e}")

    def _extract_roadmap_metadata(self, yaml_data: Dict[str, Any], file_path: Optional[str] = None) -> tuple:
        """从YAML数据中提取路线图元数据"""
        roadmap_name = None
        roadmap_description = ""
        roadmap_version = "1.0"

        # 从YAML数据中提取路线图名称
        metadata = yaml_data.get("metadata", {})
        if isinstance(metadata, dict):
            roadmap_name = metadata.get("title")
            roadmap_description = metadata.get("description", "")
            roadmap_version = metadata.get("version", "1.0")
            if self.verbose:
                logger.debug(f"从metadata中提取, 标题: {roadmap_name}, 描述: {roadmap_description}, 版本: {roadmap_version}")

        # 如果YAML中没有路线图名称，尝试从文件名推断
        if not roadmap_name and file_path:
            try:
                roadmap_name = os.path.basename(file_path)
                roadmap_name = os.path.splitext(roadmap_name)[0]  # 移除文件扩展名
                roadmap_name = roadmap_name.replace("_", " ").replace("-", " ").title()
                if self.verbose:
                    logger.debug(f"从文件名推断路线图名称: {roadmap_name}")
            except Exception as e:
                logger.warning(f"从文件名推断路线图名称失败: {str(e)}")

        # 确保有默认名称
        if not roadmap_name:
            roadmap_name = "未命名路线图"
            logger.warning(f"使用默认路线图名称: {roadmap_name}")

        return roadmap_name, roadmap_description, roadmap_version

    # def _find_existing_roadmap(self, identifier: Optional[str], name: Optional[str]) -> Optional[Dict[str, Any]]:
    #     """
    #     查找现有路线图，先按ID查找，再按名称(title)查找 (已移入 get_or_create_roadmap)
    #     ...
    #     """
    #     ...
    #     return None

    # def _create_new_roadmap(self, name: str, description: str, version: str) -> Optional[str]:
    #     """创建新路线图并返回ID (已移入 get_or_create_roadmap)"""
    #     ...
    #     return None
