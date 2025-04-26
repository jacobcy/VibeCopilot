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
        从YAML数据中获取或创建路线图，返回路线图ID

        Args:
            yaml_data: 路线图YAML数据
            file_path: YAML文件路径，用于推断路线图名称

        Returns:
            str: 路线图ID
        """
        # 提取路线图元数据
        roadmap_name, roadmap_description, roadmap_version = self._extract_roadmap_metadata(yaml_data, file_path)

        # 查找现有路线图
        roadmap_data = self._find_existing_roadmap(None, roadmap_name)
        if roadmap_data:
            roadmap_id = roadmap_data.get("id")
            if roadmap_id:
                logger.info(f"找到现有路线图: {roadmap_name}, ID: {roadmap_id}")
                return roadmap_id

        # 创建新路线图
        logger.info(f"创建新路线图: {roadmap_name}")
        roadmap_id = self._create_new_roadmap(roadmap_name, roadmap_description, roadmap_version)

        if not roadmap_id:
            raise Exception(f"创建路线图失败: {roadmap_name}")

        logger.info(f"创建新路线图成功, ID: {roadmap_id}")
        return roadmap_id

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

    def _find_existing_roadmap(self, identifier: Optional[str], name: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        查找现有路线图，先按ID查找，再按名称(title)查找

        Args:
            identifier: 路线图ID
            name: 路线图标题 (title)

        Returns:
            Optional[Dict[str, Any]]: 找到的路线图数据字典或None
        """
        roadmap_obj: Optional[Any] = None

        try:
            with session_scope() as session:
                if identifier:
                    roadmap_dict = self.service.get_roadmap(identifier)
                    if roadmap_dict:
                        self.log_info(f"通过ID找到路线图: {identifier}")
                        return roadmap_dict

                if name:
                    roadmap_obj = self.service.roadmap_repo.get_by_name(session, name)
                    if roadmap_obj:
                        self.log_info(f"发现标题匹配的路线图: {name}")
                        return self.service._object_to_dict(roadmap_obj) if hasattr(self.service, "_object_to_dict") else {"id": roadmap_obj.id}
        except Exception as e:
            self.log_error(f"查找路线图时出错: {e}", show_traceback=True)

        return None

    def _create_new_roadmap(self, name: str, description: str, version: str) -> Optional[str]:
        """创建新路线图并返回ID"""
        roadmap_obj: Optional[Any] = None
        try:
            if self.verbose:
                logger.debug(f"准备创建路线图: 标题={name}")

            roadmap_data = {
                "title": name,
                "description": description,
                "version": version,
                "status": "active",
            }

            with session_scope() as session:
                roadmap_obj = self.service.roadmap_repo.create(session, **roadmap_data)

            if not roadmap_obj or not hasattr(roadmap_obj, "id"):
                self.log_error(f"创建路线图 '{name}' 后未能获取有效对象或ID。")
                return None

            roadmap_id = roadmap_obj.id
            self.log_info(f"创建路线图成功: {roadmap_id} ({name})")
            return roadmap_id

        except Exception as e:
            self.log_error(f"创建路线图时出错: {e}", show_traceback=True)
            return None
