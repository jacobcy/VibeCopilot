"""
路线图故事处理器

处理路线图故事的创建、更新、删除和显示等操作。
"""

import json
from typing import Dict, List, Optional

from rich.console import Console
from tabulate import tabulate

from src.roadmap import RoadmapService

console = Console()


def handle_create_story(
    service: RoadmapService,
    title: str,
    milestone_id: str,
    description: Optional[str] = None,
    priority: str = "P2",
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
) -> Dict:
    """处理故事创建"""
    try:
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
            return {"success": True, "story_id": result.get("story_id"), "message": f"已创建故事: {title}"}
        else:
            return {"success": False, "message": f"创建故事失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        return {"success": False, "message": f"创建故事时出错: {str(e)}"}


def handle_update_story(
    service: RoadmapService,
    story_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    milestone_id: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
) -> Dict:
    """处理故事更新"""
    try:
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
        else:
            return {"success": False, "message": f"更新故事失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        return {"success": False, "message": f"更新故事时出错: {str(e)}"}


def handle_delete_story(service: RoadmapService, story_id: str, force: bool = False) -> Dict:
    """处理故事删除"""
    try:
        # 验证故事存在
        if not service.story_exists(story_id):
            return {"success": False, "message": f"故事不存在: {story_id}"}

        # 获取故事信息用于确认
        story = service.get_story(story_id)
        if not story:
            return {"success": False, "message": f"获取故事信息失败: {story_id}"}

        # 删除故事
        result = service.delete_story(story_id)

        if result.get("success"):
            return {"success": True, "message": f"已删除故事: {story_id}"}
        else:
            return {"success": False, "message": f"删除故事失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        return {"success": False, "message": f"删除故事时出错: {str(e)}"}


def handle_show_story(service: RoadmapService, story_id: str, format: str = "text") -> Dict:
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


def handle_update_story_status(service: RoadmapService, story_id: str, status: str, comment: Optional[str] = None) -> Dict:
    """处理故事状态更新"""
    try:
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
        else:
            return {"success": False, "message": f"更新故事状态失败: {result.get('error', '未知错误')}"}

    except Exception as e:
        return {"success": False, "message": f"更新故事状态时出错: {str(e)}"}


def handle_story_command(
    service: RoadmapService,
    story_id: Optional[str] = None,
    title: Optional[str] = None,
    milestone: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[str] = None,
    status: Optional[str] = None,
    comment: Optional[str] = None,
    format: str = "text",
    delete: bool = False,
    force: bool = False,
) -> Dict:
    """统一处理故事命令的入口函数"""
    try:
        # 如果是删除操作
        if delete:
            if not story_id:
                return {"success": False, "message": "删除操作需要指定故事ID"}
            return handle_delete_story(service, story_id, force)

        # 如果指定了story_id但没有其他参数，显示故事信息
        if story_id and not any([title, milestone, description, priority, assignee, labels, status]):
            return handle_show_story(service, story_id, format)

        # 如果指定了status，更新故事状态
        if status and story_id:
            return handle_update_story_status(service, story_id, status, comment)

        # 如果有story_id，更新故事
        if story_id:
            labels_list = labels.split(",") if labels else None
            return handle_update_story(
                service=service,
                story_id=story_id,
                title=title,
                description=description,
                milestone_id=milestone,
                priority=priority,
                assignee=assignee,
                labels=labels_list,
            )

        # 创建新故事
        if title and milestone:
            labels_list = labels.split(",") if labels else None
            return handle_create_story(
                service=service,
                title=title,
                milestone_id=milestone,
                description=description,
                priority=priority or "P2",
                assignee=assignee,
                labels=labels_list,
            )

        return {"success": False, "message": "无效的命令参数组合"}

    except Exception as e:
        return {"success": False, "message": f"处理故事命令时出错: {str(e)}"}
