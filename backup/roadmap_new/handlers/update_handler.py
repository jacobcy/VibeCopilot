"""
路线图更新命令处理程序

处理更新路线图或路线图元素状态的命令逻辑。
"""

from typing import Any, Dict, Optional

from rich.console import Console

console = Console()


def handle_update_command(args: Dict[str, Any], service) -> Dict[str, Any]:
    """处理路线图更新命令

    Args:
        args: 命令参数字典
        service: 路线图服务实例

    Returns:
        Dict[str, Any]: 处理结果
    """
    element_id = args.get("id")
    if not element_id:
        return {"status": "error", "message": "必须提供要更新的元素ID"}

    # 获取更新参数
    element_type = args.get("type")
    status = args.get("status")
    name = args.get("name")
    description = args.get("description")
    priority = args.get("priority")
    assignee = args.get("assignee")
    labels = args.get("labels")
    start_date = args.get("start_date")
    end_date = args.get("end_date")

    # 如果没有提供任何更新参数
    if not any([status, name, description, priority, assignee, labels, start_date, end_date]):
        return {"status": "error", "message": "必须提供至少一个要更新的属性(status/name/description/priority/assignee/labels/start_date/end_date)"}

    # 如果没有指定类型，尝试根据ID格式猜测类型
    if not element_type:
        element_type = _guess_element_type(element_id, service)
        if not element_type:
            return {"status": "error", "message": "无法确定元素类型，请使用--type指定(roadmap/milestone/story/task)"}

    # 准备更新数据
    update_data = {}
    if status:
        update_data["status"] = status
    if name:
        update_data["name"] = name
    if description:
        update_data["description"] = description
    if priority:
        update_data["priority"] = priority
    if assignee:
        update_data["assignee"] = assignee
    if labels:
        # 转换标签字符串为列表
        update_data["labels"] = [label.strip() for label in labels.split(",")]
    if start_date:
        update_data["start_date"] = start_date
    if end_date:
        update_data["end_date"] = end_date

    # 执行更新操作
    result = _perform_update(element_type, element_id, update_data, service)

    if result.get("success", False):
        return {"status": "success", "message": result.get("message", f"成功更新{_get_type_display_name(element_type)}")}
    else:
        return {"status": "error", "message": result.get("error", f"更新{_get_type_display_name(element_type)}失败")}


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


def _get_type_display_name(element_type: str) -> str:
    """获取元素类型的友好显示名称"""
    type_names = {"roadmap": "路线图", "milestone": "里程碑", "story": "故事", "task": "任务"}
    return type_names.get(element_type, element_type)


def _perform_update(element_type: str, element_id: str, update_data: Dict[str, Any], service) -> Dict[str, Any]:
    """执行实际的更新操作"""
    try:
        # 获取当前活动路线图ID (如果更新的不是路线图本身)
        roadmap_id = None
        if element_type != "roadmap":
            roadmap_id = service.active_roadmap_id
            if not roadmap_id:
                return {"success": False, "error": "未设置活动路线图，无法更新路线图元素。请先使用'roadmap switch <roadmap_id>'设置活动路线图。"}

        # 根据元素类型执行不同的更新操作
        if element_type == "roadmap":
            result = service.update_roadmap(element_id, update_data)
            return {"success": result.get("success", False), "message": f"成功更新路线图 (ID: {element_id})", "error": result.get("error", "更新路线图失败")}

        elif element_type == "milestone":
            result = service.update_milestone(element_id, roadmap_id, update_data)
            return {"success": result.get("success", False), "message": f"成功更新里程碑 (ID: {element_id})", "error": result.get("error", "更新里程碑失败")}

        elif element_type == "story":
            result = service.update_story(element_id, roadmap_id, update_data)
            return {"success": result.get("success", False), "message": f"成功更新故事 (ID: {element_id})", "error": result.get("error", "更新故事失败")}

        elif element_type == "task":
            result = service.update_task(element_id, roadmap_id, update_data)
            return {"success": result.get("success", False), "message": f"成功更新任务 (ID: {element_id})", "error": result.get("error", "更新任务失败")}

        else:
            return {"success": False, "error": f"不支持的元素类型: {element_type}"}

    except Exception as e:
        return {"success": False, "error": f"更新过程中发生错误: {str(e)}"}
