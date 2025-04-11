"""
路线图删除处理器

处理路线图及其元素的删除操作
"""

from typing import Dict, Optional, Tuple

from rich.console import Console

from src.roadmap import RoadmapService

console = Console()


def get_type_name(type: str) -> str:
    """获取类型名称"""
    mapping = {"roadmap": "路线图", "milestone": "里程碑", "story": "故事", "task": "任务"}
    return mapping.get(type, type)


def get_object_name(service: RoadmapService, type: str, id: str) -> str:
    """获取对象名称"""
    try:
        if type == "roadmap":
            obj = service.get_roadmap(id)
            return obj.get("title", "未命名路线图")
        elif type == "milestone":
            obj = service.get_milestone(id)
            return obj.get("title", "未命名里程碑")
        elif type == "story":
            obj = service.get_story(id)
            return obj.get("title", "未命名故事")
        elif type == "task":
            obj = service.get_task(id)
            return obj.get("title", "未命名任务")
        return "未知对象"
    except:
        return "未命名对象"


def handle_delete(service: RoadmapService, type: str, id: str, cascade: bool = False) -> Dict:
    """
    处理删除操作

    Args:
        service: RoadmapService实例
        type: 要删除的对象类型
        id: 对象ID
        cascade: 是否级联删除

    Returns:
        Dict: 包含操作结果的字典
    """
    try:
        # 执行删除
        if type == "roadmap":
            result = service.delete_roadmap(id, cascade=cascade)
        elif type == "milestone":
            result = service.delete_milestone(id, cascade=cascade)
        elif type == "story":
            result = service.delete_story(id)
        elif type == "task":
            result = service.delete_task(id)
        else:
            return {"success": False, "message": f"不支持的类型: {type}"}

        return result

    except Exception as e:
        return {"success": False, "message": str(e)}
