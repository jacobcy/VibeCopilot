"""
路线图删除命令处理程序

处理删除路线图或路线图元素的命令逻辑。
"""

from typing import Any, Dict

from rich.console import Console
from rich.prompt import Confirm

console = Console()


def handle_delete_command(args: Dict[str, Any], service) -> Dict[str, Any]:
    """处理路线图删除命令

    Args:
        args: 命令参数字典
        service: 路线图服务实例

    Returns:
        Dict[str, Any]: 处理结果
    """
    element_type = args.get("type")
    element_id = args.get("id")
    force = args.get("force", False)
    cascade = args.get("cascade", False)

    if not element_id:
        return {"status": "error", "message": "必须提供要删除的元素ID"}

    if not element_type:
        # 如果没有指定类型，尝试通过ID识别类型
        element_type = _guess_element_type(element_id, service)

        if not element_type:
            return {"status": "error", "message": "无法识别元素类型，请使用--type参数明确指定类型(roadmap/milestone/story/task)"}

    # 在非强制模式下请求确认
    if not force:
        # 获取元素名称以便在确认提示中显示
        element_name = _get_element_name(element_type, element_id, service)
        confirm_message = f"是否确定要删除{_get_type_display_name(element_type)} '{element_name}' (ID: {element_id})?"

        if cascade:
            confirm_message += " 这将同时删除所有关联的子元素！"

        # 询问用户确认
        if not Confirm.ask(confirm_message):
            return {"status": "cancelled", "message": "已取消删除操作"}

    # 执行删除操作
    result = _perform_delete(element_type, element_id, service, cascade)

    if result.get("success", False):
        return {"status": "success", "message": result.get("message", f"成功删除{_get_type_display_name(element_type)}")}
    else:
        return {"status": "error", "message": result.get("error", f"删除{_get_type_display_name(element_type)}失败")}


def _guess_element_type(element_id: str, service) -> str:
    """尝试根据ID格式猜测元素类型"""
    # 获取当前活动路线图ID
    active_roadmap_id = service.active_roadmap_id

    # 检查是否是路线图ID
    if element_id == active_roadmap_id:
        return "roadmap"

    # 检查ID前缀，许多系统会用不同前缀区分不同类型
    if element_id.startswith("ms-") or element_id.startswith("milestone-"):
        return "milestone"

    if element_id.startswith("story-") or element_id.startswith("s-"):
        return "story"

    if element_id.startswith("task-") or element_id.startswith("t-"):
        return "task"

    # 无法确定类型
    return ""


def _get_element_name(element_type: str, element_id: str, service) -> str:
    """获取元素名称以供显示"""
    if element_type == "roadmap":
        roadmap = service.get_roadmap(element_id)
        if roadmap:
            return roadmap.get("name") or roadmap.get("title") or "[未命名路线图]"

    elif element_type == "milestone":
        # 获取当前活动路线图
        roadmap_id = service.active_roadmap_id
        milestones = service.get_milestones(roadmap_id)
        milestone = next((m for m in milestones if m.get("id") == element_id), None)
        if milestone:
            return milestone.get("name") or "[未命名里程碑]"

    elif element_type == "story":
        # 获取当前活动路线图
        roadmap_id = service.active_roadmap_id
        stories = service.get_stories(roadmap_id)
        story = next((s for s in stories if s.get("id") == element_id), None)
        if story:
            return story.get("title") or "[未命名故事]"

    elif element_type == "task":
        # 获取当前活动路线图
        roadmap_id = service.active_roadmap_id
        tasks = service.get_tasks(roadmap_id)
        task = next((t for t in tasks if t.get("id") == element_id), None)
        if task:
            return task.get("name") or task.get("title") or "[未命名任务]"

    return f"[未知{_get_type_display_name(element_type)}]"


def _get_type_display_name(element_type: str) -> str:
    """获取元素类型的友好显示名称"""
    type_names = {"roadmap": "路线图", "milestone": "里程碑", "story": "故事", "task": "任务"}
    return type_names.get(element_type, element_type)


def _perform_delete(element_type: str, element_id: str, service, cascade: bool = False) -> Dict[str, Any]:
    """执行实际的删除操作"""
    try:
        if element_type == "roadmap":
            result = service.delete_roadmap(element_id)
            return {"success": result.get("success", False), "message": f"成功删除路线图 (ID: {element_id})", "error": result.get("error", "删除路线图失败")}

        elif element_type == "milestone":
            result = service.delete_milestone(element_id, cascade)
            return {"success": result.get("success", False), "message": f"成功删除里程碑 (ID: {element_id})", "error": result.get("error", "删除里程碑失败")}

        elif element_type == "story":
            result = service.delete_story(element_id, cascade)
            return {"success": result.get("success", False), "message": f"成功删除故事 (ID: {element_id})", "error": result.get("error", "删除故事失败")}

        elif element_type == "task":
            result = service.delete_task(element_id)
            return {"success": result.get("success", False), "message": f"成功删除任务 (ID: {element_id})", "error": result.get("error", "删除任务失败")}

        else:
            return {"success": False, "error": f"不支持的元素类型: {element_type}"}

    except Exception as e:
        return {"success": False, "error": f"删除过程中发生错误: {str(e)}"}
