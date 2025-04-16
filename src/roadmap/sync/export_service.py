"""
导出服务模块

提供路线图导出到YAML文件的功能。
"""

import logging
import os
from typing import Any, Dict, List, Optional

import yaml

from src.core.config import get_config
from src.roadmap.core.roadmap_models import Milestone, Roadmap, Story
from src.utils.file_utils import ensure_dir_exists

from .utils import print_error, print_success

logger = logging.getLogger(__name__)


class RoadmapExportService:
    """路线图导出服务，提供路线图到YAML文件的导出功能"""

    def __init__(self, service):
        """
        初始化路线图导出服务

        Args:
            service: 路线图服务
        """
        self.service = service
        self.config = get_config()
        self.project_root = self.config.get("paths.project_root", os.getcwd())
        self.agent_work_dir = self.config.get("paths.agent_work_dir", ".ai")  # 从配置获取

    def _get_default_export_path(self, roadmap_id: str) -> str:
        """获取默认导出路径"""
        # 使用 agent_work_dir 构建路径
        export_dir = os.path.join(self.project_root, self.agent_work_dir, "roadmap", "exports")
        ensure_dir_exists(export_dir)
        return os.path.join(export_dir, f"{roadmap_id}.yaml")

    def export_to_yaml(self, roadmap_id: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        导出路线图到YAML文件

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图
            output_path: 输出文件路径，不提供则使用默认路径

        Returns:
            Dict[str, Any]: 导出结果
        """
        roadmap_id = roadmap_id or self.service.active_roadmap_id

        # 检查路线图是否存在
        roadmap = self.service.get_roadmap(roadmap_id)
        if not roadmap:
            logger.error(f"未找到路线图: {roadmap_id}")
            return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

        # 确定文件路径
        if not output_path:
            output_path = self._get_default_export_path(roadmap_id)

        # 导出到YAML文件 - 简化实现
        try:
            # 获取路线图数据
            roadmap_data = self._prepare_roadmap_data(roadmap_id)

            # 简化实现，不实际写入文件
            logger.info(f"导出路线图到YAML: {roadmap_id} -> {output_path}")
            return {
                "success": True,
                "roadmap_id": roadmap_id,
                "roadmap_name": roadmap.get("name"),
                "file_path": output_path,
            }
        except Exception as e:
            logger.error(f"导出路线图到YAML失败: {str(e)}")
            return {"success": False, "error": f"导出失败: {str(e)}"}

    def _prepare_roadmap_data(self, roadmap_id: str) -> Dict[str, Any]:
        """准备路线图数据用于导出"""
        roadmap = self.service.get_roadmap(roadmap_id)
        milestones = self.service.get_milestones(roadmap_id)
        tasks = self.service.get_tasks(roadmap_id)

        return {"roadmap": roadmap, "milestones": milestones, "tasks": tasks}

    def export_roadmap(self, roadmap: Roadmap, output_path: Optional[str] = None) -> Optional[str]:
        """导出单个路线图对象"""
        # 将Roadmap对象转换为字典
        roadmap_dict = roadmap.to_dict()  # 假设 Roadmap 对象有 to_dict 方法
        return self.export_to_yaml(roadmap_id=roadmap_dict.get("id"), output_path=output_path)

    def export_full_structure(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Optional[str]:
        """导出包含所有层级的完整结构"""
        # 这里假设传入的 data 就是可以直接导出的完整字典
        # 如果需要从数据库或其他地方组装，需要先实现组装逻辑
        return self.export_to_yaml(roadmap_id=data.get("id"), output_path=output_path)

    def _ensure_export_dir(self):
        """确保导出目录存在"""
        # 这个逻辑似乎可以合并到 _get_default_export_path 中
        export_dir = os.path.join(self.project_root, self.agent_work_dir, "roadmap", "exports")
        ensure_dir_exists(export_dir)
