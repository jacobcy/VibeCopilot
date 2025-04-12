"""
路线图创建处理器

处理路线图元素（里程碑、史诗、故事）的创建操作。
"""

from typing import Any, Dict, List, Optional

from rich.console import Console

from src.roadmap import RoadmapService

console = Console()


def handle_create_element(
    service: RoadmapService,
    type: str,
    title: str,
    epic_id: Optional[str] = None,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    priority: Optional[str] = None,
) -> Dict[str, Any]:
    """处理路线图元素创建

    Args:
        service: RoadmapService实例
        type: 元素类型 ('milestone', 'epic', 'story')
        title: 元素标题
        epic_id: 史诗ID（用于story）
        description: 详细描述
        assignee: 指派人
        labels: 标签列表
        priority: 优先级（用于epic）
    """
    try:
        # 准备创建参数
        create_params = {
            "title": title,
            "description": description or "",
            "assignee": assignee,
            "labels": labels or [],
        }

        # 根据元素类型添加特定参数
        if type == "story":
            if not epic_id:
                return {"success": False, "message": "创建story需要指定所属epic的ID"}
            create_params["epic_id"] = epic_id
        elif type == "epic":
            if priority:
                create_params["priority"] = priority

        # 调用相应的服务方法
        if type == "milestone":
            result = service.create_milestone(create_params)
        elif type == "epic":
            result = service.create_epic(create_params)
        else:  # story
            result = service.create_story(create_params)

        if not result.get("success", False):
            return {"success": False, "message": f"创建{type}失败: {result.get('message', '未知错误')}"}

        return {
            "success": True,
            "message": f"已创建{type}: {title}",
            "data": {"type": type, "id": result["data"].get("id"), "title": result["data"].get("title")},
        }

    except Exception as e:
        return {"success": False, "message": f"创建{type}时出错: {str(e)}"}
