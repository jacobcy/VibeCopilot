"""
路线图故事处理器

处理路线图故事的创建、更新、删除和显示等操作。
使用模块化设计，每个函数专注于单一职责。
"""

import json
from typing import Any, Dict, List, Literal, Optional

from rich.console import Console
from tabulate import tabulate

from src.roadmap import RoadmapService

from .delete_handlers import handle_delete

console = Console()

# 常量定义
STORY_PRIORITIES = ["P0", "P1", "P2", "P3"]
STORY_STATUSES = ["not_started", "in_progress", "completed", "blocked"]


def handle_story_command(
    service: RoadmapService,
    story_id: Optional[str] = None,
    title: Optional[str] = None,
    milestone_id: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[str] = None,
    status: Optional[str] = None,
    comment: Optional[str] = None,
    format: str = "text",
    delete: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """统一处理故事命令的入口函数"""
    try:
        # 处理删除操作
        if delete and story_id:
            return handle_story_delete(service, story_id, force)

        # 处理创建操作
        if title and milestone_id and not story_id:
            return handle_story_create(
                service=service,
                title=title,
                milestone_id=milestone_id,
                description=description,
                priority=priority or "P2",
                assignee=assignee,
                labels=labels.split(",") if labels else None,
            )

        # 处理更新操作
        if story_id and (title or description or milestone_id or priority or assignee or labels):
            return handle_story_update(
                service=service,
                story_id=story_id,
                title=title,
                description=description,
                milestone_id=milestone_id,
                priority=priority,
                assignee=assignee,
                labels=labels.split(",") if labels else None,
            )

        # 处理状态更新
        if story_id and status:
            return handle_story_status_update(service=service, story_id=story_id, status=status, comment=comment)

        # 处理显示操作
        if story_id:
            return handle_story_show(service=service, story_id=story_id, format=format)

        return {"success": False, "message": "请提供必要的参数来执行具体操作"}

    except Exception as e:
        return {"success": False, "message": f"执行出错: {str(e)}"}


def handle_story_create(
    service: RoadmapService,
    title: str,
    milestone_id: str,
    description: Optional[str] = None,
    priority: str = "P2",
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """处理故事创建"""
    try:
        # 验证参数
        if priority not in STORY_PRIORITIES:
            return {"success": False, "message": f"无效的优先级: {priority}"}

        # 验证里程碑存在
        if not service.milestone_exists(milestone_id):
            return {"success": False, "message": f"里程碑不存在: {milestone_id}"}

        # 创建故事
        result = service.create_story(
            title=title,
            milestone_id=milestone_id,
            description=description,
            priority=priority,
            assignee=assignee,
            labels=labels or [],
        )

        if result.get("success"):
            return {"success": True, "message": f"已创建故事: {title}", "data": {"story_id": result.get("story_id")}}

        return {"success": False, "message": f"创建故事失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        return {"success": False, "message": f"创建故事时出错: {str(e)}"}


def handle_story_update(
    service: RoadmapService,
    story_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    milestone_id: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """处理故事更新"""
    try:
        # 验证参数
        if priority and priority not in STORY_PRIORITIES:
            return {"success": False, "message": f"无效的优先级: {priority}"}

        # 验证故事存在
        if not service.story_exists(story_id):
            return {"success": False, "message": f"故事不存在: {story_id}"}

        # 如果指定了新里程碑，验证其存在性
        if milestone_id and not service.milestone_exists(milestone_id):
            return {"success": False, "message": f"里程碑不存在: {milestone_id}"}

        # 更新故事
        result = service.update_story(
            story_id=story_id,
            title=title,
            description=description,
            milestone_id=milestone_id,
            priority=priority,
            assignee=assignee,
            labels=labels,
        )

        if result.get("success"):
            return {"success": True, "message": f"已更新故事: {story_id}"}

        return {"success": False, "message": f"更新故事失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        return {"success": False, "message": f"更新故事时出错: {str(e)}"}


def handle_story_delete(service: RoadmapService, story_id: str, force: bool = False) -> Dict[str, Any]:
    """处理故事删除"""
    return handle_delete(service, "story", story_id, force)


def handle_story_show(service: RoadmapService, story_id: str, format: Literal["json", "text", "table"] = "text") -> Dict[str, Any]:
    """处理故事显示"""
    try:
        # 获取故事信息
        story = service.get_story(story_id)
        if not story:
            return {"success": False, "message": f"故事不存在: {story_id}"}

        if format == "json":
            formatted_output = json.dumps(story, indent=2, ensure_ascii=False)
        elif format == "table":
            headers = ["属性", "值"]
            rows = [
                ["ID", story_id],
                ["标题", story.get("title", "")],
                ["描述", story.get("description", "")],
                ["里程碑", story.get("milestone_id", "")],
                ["优先级", story.get("priority", "")],
                ["指派人", story.get("assignee", "")],
                ["标签", ", ".join(story.get("labels", []))],
                ["状态", story.get("status", "")],
                ["创建时间", story.get("created_at", "")],
                ["更新时间", story.get("updated_at", "")],
            ]
            formatted_output = tabulate(rows, headers=headers, tablefmt="grid")
        else:
            # 文本格式
            output = []
            output.append(f"故事: {story.get('title')} ({story_id})")
            output.append(f"描述: {story.get('description', '')}")
            output.append(f"里程碑: {story.get('milestone_id', '')}")
            output.append(f"优先级: {story.get('priority', '')}")
            output.append(f"指派人: {story.get('assignee', '')}")
            if story.get("labels"):
                output.append(f"标签: {', '.join(story.get('labels', []))}")
            output.append(f"状态: {story.get('status', '')}")
            output.append(f"创建时间: {story.get('created_at', '')}")
            output.append(f"更新时间: {story.get('updated_at', '')}")
            formatted_output = "\n".join(output)

        return {"success": True, "data": {"story": story, "formatted_output": formatted_output}}

    except Exception as e:
        return {"success": False, "message": f"显示故事时出错: {str(e)}"}


def handle_story_status_update(service: RoadmapService, story_id: str, status: str, comment: Optional[str] = None) -> Dict[str, Any]:
    """处理故事状态更新"""
    try:
        # 验证参数
        if status not in STORY_STATUSES:
            return {"success": False, "message": f"无效的状态值: {status}"}

        # 验证故事存在
        if not service.story_exists(story_id):
            return {"success": False, "message": f"故事不存在: {story_id}"}

        # 更新状态
        result = service.update_story_status(
            story_id=story_id,
            status=status,
            comment=comment,
        )

        if result.get("success"):
            return {"success": True, "message": f"已更新故事状态为 {status}: {story_id}"}

        return {"success": False, "message": f"更新故事状态失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        return {"success": False, "message": f"更新故事状态时出错: {str(e)}"}
