"""
路线图操作处理器模块

提供路线图操作的处理逻辑，直接调用底层服务。
"""

from typing import Any, Dict, Optional


def export_to_yaml(service, roadmap_id: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    导出路线图到YAML文件

    直接调用export_service.export_to_yaml，避免多层调用链

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图
        output_path: 输出文件路径，不提供则使用默认路径

    Returns:
        Dict[str, Any]: 导出结果
    """
    # 直接从export_service导入RoadmapExportService
    from src.roadmap.sync.export_service import RoadmapExportService

    # 创建导出服务实例并直接调用
    export_service = RoadmapExportService(service)
    return export_service.export_to_yaml(roadmap_id, output_path)
