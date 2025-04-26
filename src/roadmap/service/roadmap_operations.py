"""
路线图操作模块

提供路线图的创建、更新、删除和同步功能。
"""

import logging
from typing import Any, Dict, Optional

from src.db.session_manager import session_scope

logger = logging.getLogger(__name__)


def delete_roadmap(service, roadmap_id: str) -> Dict[str, Any]:
    """
    删除路线图

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID

    Returns:
        Dict[str, Any]: 删除结果
    """
    try:
        # 检查路线图是否存在 - 使用 session
        with session_scope() as session:
            roadmap_obj = service.roadmap_repo.get_by_id(session, roadmap_id)
            if not roadmap_obj:
                return {"success": False, "error": f"未找到路线图: {roadmap_id}"}
            roadmap_name = roadmap_obj.title  # Get name before potential deletion

        # 检查是否是活跃路线图 (在 session 外检查，避免持有 session)
        active_id = service.active_roadmap_id
        if roadmap_id == active_id:
            return {"success": False, "error": "不能删除当前活跃路线图，请先切换到其他路线图"}

        # 删除路线图及其所有内容 - 使用 session
        try:
            with session_scope() as session:
                # 调用 delete 时传递 session 和 id
                deleted = service.roadmap_repo.delete(session, roadmap_id)
                if deleted:
                    logger.info(f"删除路线图: {roadmap_name} (ID: {roadmap_id})")
                    return {"success": True, "roadmap_id": roadmap_id, "roadmap_name": roadmap_name}
                else:
                    # Repository delete should return False if not found, but we checked above
                    logger.warning(f"尝试删除路线图 {roadmap_id} 时，delete 方法返回 False。")
                    return {"success": False, "error": "删除路线图失败 (Repository 返回 False)"}
        except Exception as e:
            logger.error(f"删除路线图时数据库操作出错: {e}", exc_info=True)
            return {"success": False, "error": f"数据库错误: {str(e)}"}

    except Exception as e:
        logger.error(f"删除路线图前检查时出错: {e}", exc_info=True)
        return {"success": False, "error": f"检查路线图时出错: {str(e)}"}


def sync_to_github(service, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
    """
    同步路线图到GitHub

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        Dict[str, Any]: 同步结果
    """
    roadmap_id = roadmap_id or service.active_roadmap_id

    # 同步到GitHub
    result = service.github_sync.sync_roadmap_to_github(roadmap_id)

    return result


def sync_from_github(service, repo_name: str, branch: str = "main", theme: Optional[str] = None, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
    """
    从GitHub同步数据到路线图

    Args:
        service: 路线图服务实例
        repo_name: GitHub仓库名称（格式：owner/repo）
        branch: 要同步的分支名称，默认为main
        theme: GitHub项目主题标签，用于筛选特定主题的问题
        roadmap_id: 路线图ID，不提供则使用活跃路线图或创建新路线图

    Returns:
        Dict[str, Any]: 同步结果
    """
    roadmap_id = roadmap_id or service.active_roadmap_id

    # 从GitHub同步
    result = service.github_sync.sync_from_github(repo_name, branch, theme, roadmap_id)

    return result


def export_to_yaml(service, roadmap_id: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    导出路线图到YAML文件

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
