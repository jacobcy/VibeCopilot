"""
YAML同步服务模块

提供与YAML文件的同步功能。
"""

import logging
from typing import Any, Dict, Optional

from .export_service import RoadmapExportService
from .import_service import RoadmapImportService

logger = logging.getLogger(__name__)


class YamlSyncService:
    """YAML同步服务，提供路线图与YAML文件的同步功能"""

    def __init__(self, service):
        """
        初始化YAML同步服务

        Args:
            service: 路线图服务
        """
        self.service = service
        self.export_service = RoadmapExportService(service)
        self.import_service = RoadmapImportService(service)

    def export_to_yaml(self, roadmap_id: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        导出路线图到YAML文件

        Args:
            roadmap_id: 路线图ID，不提供则使用活跃路线图
            output_path: 输出文件路径，不提供则使用默认路径

        Returns:
            Dict[str, Any]: 导出结果
        """
        return self.export_service.export_to_yaml(roadmap_id, output_path)

    def import_from_yaml(self, file_path: str, roadmap_id: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
        """
        从YAML文件导入路线图数据

        Args:
            file_path: YAML文件路径
            roadmap_id: 路线图ID，不提供则创建新路线图
            verbose: 是否启用详细日志

        Returns:
            Dict[str, Any]: 导入结果
        """
        return self.import_service.import_from_yaml(file_path, roadmap_id, verbose)
