"""
路线图切换处理器

处理路线图的切换、显示和清除等操作。
"""

from typing import Any, Dict, Optional

from rich.console import Console

from src.roadmap import RoadmapService

console = Console()


def handle_switch_roadmap(service: RoadmapService, roadmap_id: Optional[str] = None, show: bool = False, clear: bool = False) -> Dict[str, Any]:
    """处理路线图切换操作"""
    try:
        # 处理清除操作
        if clear:
            success = service.set_active_roadmap(None)
            if success:
                return {"success": True, "message": "已清除当前活动路线图"}
            else:
                return {"success": False, "message": "清除活动路线图失败"}

        # 处理显示操作
        if show or not roadmap_id:
            active_id = service.active_roadmap_id
            if not active_id:
                return {"success": True, "message": "当前未设置活动路线图"}

            roadmap = service.get_roadmap(active_id)
            if not roadmap:
                return {"success": False, "message": f"当前活动路线图 {active_id} 不存在或无法访问"}

            return {
                "success": True,
                "message": f"当前活动路线图: {roadmap.get('title', '[未命名]')} ({active_id})",
                "data": {"roadmap_id": active_id, "roadmap": roadmap},
            }

        # 处理切换操作
        roadmap = service.get_roadmap(roadmap_id)
        if not roadmap:
            return {"success": False, "message": f"路线图不存在: {roadmap_id}"}

        service.set_active_roadmap(roadmap_id)
        return {
            "success": True,
            "message": f"已切换到路线图: {roadmap.get('title', '[未命名]')} ({roadmap_id})",
            "data": {"roadmap_id": roadmap_id, "roadmap": roadmap},
        }

    except Exception as e:
        return {"success": False, "message": f"执行出错: {str(e)}"}
