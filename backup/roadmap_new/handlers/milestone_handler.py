"""
命令处理模块 - 管理路线图里程碑相关操作

此模块实现路线图里程碑的命令处理逻辑，包括创建、更新、删除和查看里程碑的功能
"""

import json
from typing import Any, Dict, List, Optional

from src.roadmap.service import RoadmapService


def handle_milestone_command(args, roadmap_service: RoadmapService = None):
    """
    处理里程碑相关命令

    参数:
        args: 命令参数
        roadmap_service: 路线图服务实例

    返回:
        包含操作结果和格式化输出的字典
    """
    if not roadmap_service:
        roadmap_service = RoadmapService()

    # 确定子命令类型
    sub_command = args.get("sub_command")

    if sub_command == "create":
        return _create_milestone(roadmap_service, args)
    elif sub_command == "update":
        return _update_milestone(roadmap_service, args)
    elif sub_command == "delete":
        return _delete_milestone(roadmap_service, args)
    elif sub_command == "list":
        return _list_milestones(roadmap_service, args)
    elif sub_command == "get":
        return _get_milestone(roadmap_service, args)
    else:
        return {
            "status": "error",
            "message": f"未知的里程碑命令: {sub_command}",
            "formatted_output": f"错误: 未知的里程碑命令: {sub_command}\n可用命令: create, update, delete, list, get",
        }


def _create_milestone(service: RoadmapService, args: Dict) -> Dict:
    """
    创建新的里程碑

    参数:
        service: 路线图服务实例
        args: 命令参数

    返回:
        操作结果字典
    """
    # 获取必要参数
    roadmap_id = args.get("roadmap_id")
    name = args.get("name")
    format_type = args.get("format", "table")

    # 首先检查是否有提供路线图ID，如果没有则尝试使用当前活动路线图
    if not roadmap_id:
        roadmap_id = service.active_roadmap_id

        # 如果依然没有路线图ID，提供友好提示
        if not roadmap_id:
            message = """[yellow]当前未指定路线图ID，且未设置活动路线图[/yellow]

可以通过以下命令操作:
[blue]1. 查看所有可用路线图:[/blue]
   roadmap list --all

[blue]2. 切换到活动路线图:[/blue]
   roadmap switch <roadmap_id>

[blue]3. 指定路线图ID执行里程碑命令:[/blue]
   milestone <sub_command> --roadmap-id=<roadmap_id> ...其他参数"""

            return {"status": "success", "message": "未指定路线图ID，且未设置活动路线图", "formatted_output": message}  # 改为success而非error

    if not name:
        return {"status": "error", "message": "缺少里程碑名称", "formatted_output": "错误: 请提供里程碑名称"}

    # 准备里程碑数据
    milestone_data = {
        "name": name,
        "description": args.get("description", ""),
        "due_date": args.get("due_date"),
        "status": args.get("status", "pending"),
    }

    # 创建里程碑
    result = service.create_milestone(roadmap_id, milestone_data)

    if not result or "error" in result:
        error_msg = result.get("error", "未知错误") if result else "创建里程碑失败"
        return {"status": "error", "message": error_msg, "formatted_output": f"错误: {error_msg}"}

    # 格式化输出
    if format_type == "json":
        return {"status": "success", "data": result, "formatted_output": json.dumps(result, indent=2, ensure_ascii=False)}

    if format_type == "text":
        milestone_id = result.get("id", "未知ID")
        milestone_name = result.get("name", "未命名里程碑")
        return {"status": "success", "data": result, "formatted_output": f"里程碑创建成功: {milestone_name} (ID: {milestone_id})"}

    # 默认表格格式
    return {"status": "success", "data": result, "formatted_output": _format_milestone_table(result, roadmap_id)}


def _update_milestone(service: RoadmapService, args: Dict) -> Dict:
    """
    更新里程碑信息

    参数:
        service: 路线图服务实例
        args: 命令参数

    返回:
        操作结果字典
    """
    # 获取必要参数
    roadmap_id = args.get("roadmap_id")
    milestone_id = args.get("milestone_id")
    format_type = args.get("format", "table")

    # 首先检查是否有提供路线图ID，如果没有则尝试使用当前活动路线图
    if not roadmap_id:
        roadmap_id = service.active_roadmap_id

        # 如果依然没有路线图ID，提供友好提示
        if not roadmap_id:
            message = """[yellow]当前未指定路线图ID，且未设置活动路线图[/yellow]

可以通过以下命令操作:
[blue]1. 查看所有可用路线图:[/blue]
   roadmap list --all

[blue]2. 切换到活动路线图:[/blue]
   roadmap switch <roadmap_id>

[blue]3. 指定路线图ID执行里程碑命令:[/blue]
   milestone update --roadmap-id=<roadmap_id> --milestone-id=<milestone_id> ...其他参数"""

            return {"status": "success", "message": "未指定路线图ID，且未设置活动路线图", "formatted_output": message}  # 改为success而非error

    if not milestone_id:
        return {"status": "error", "message": "缺少里程碑ID", "formatted_output": "错误: 请提供里程碑ID"}

    # 准备更新数据
    update_data = {}

    if "name" in args:
        update_data["name"] = args["name"]

    if "description" in args:
        update_data["description"] = args["description"]

    if "due_date" in args:
        update_data["due_date"] = args["due_date"]

    if "status" in args:
        update_data["status"] = args["status"]

    # 如果没有任何更新数据
    if not update_data:
        return {"status": "error", "message": "没有提供任何更新字段", "formatted_output": "错误: 请提供至少一个要更新的字段 (name, description, due_date, status)"}

    # 更新里程碑
    result = service.update_milestone(roadmap_id, milestone_id, update_data)

    if not result or "error" in result:
        error_msg = result.get("error", "未知错误") if result else "更新里程碑失败"
        return {"status": "error", "message": error_msg, "formatted_output": f"错误: {error_msg}"}

    # 格式化输出
    if format_type == "json":
        return {"status": "success", "data": result, "formatted_output": json.dumps(result, indent=2, ensure_ascii=False)}

    if format_type == "text":
        milestone_name = result.get("name", "未命名里程碑")
        return {"status": "success", "data": result, "formatted_output": f"里程碑更新成功: {milestone_name} (ID: {milestone_id})"}

    # 默认表格格式
    return {"status": "success", "data": result, "formatted_output": _format_milestone_table(result, roadmap_id)}


def _delete_milestone(service: RoadmapService, args: Dict) -> Dict:
    """
    删除里程碑

    参数:
        service: 路线图服务实例
        args: 命令参数

    返回:
        操作结果字典
    """
    # 获取必要参数
    roadmap_id = args.get("roadmap_id")
    milestone_id = args.get("milestone_id")
    format_type = args.get("format", "table")

    # 首先检查是否有提供路线图ID，如果没有则尝试使用当前活动路线图
    if not roadmap_id:
        roadmap_id = service.active_roadmap_id

        # 如果依然没有路线图ID，提供友好提示
        if not roadmap_id:
            message = """[yellow]当前未指定路线图ID，且未设置活动路线图[/yellow]

可以通过以下命令操作:
[blue]1. 查看所有可用路线图:[/blue]
   roadmap list --all

[blue]2. 切换到活动路线图:[/blue]
   roadmap switch <roadmap_id>

[blue]3. 指定路线图ID执行里程碑命令:[/blue]
   milestone delete --roadmap-id=<roadmap_id> --milestone-id=<milestone_id>"""

            return {"status": "success", "message": "未指定路线图ID，且未设置活动路线图", "formatted_output": message}  # 改为success而非error

    if not milestone_id:
        return {"status": "error", "message": "缺少里程碑ID", "formatted_output": "错误: 请提供里程碑ID"}

    # 删除前先获取里程碑信息，用于显示
    milestone = service.get_milestone(roadmap_id, milestone_id)

    if not milestone:
        return {"status": "error", "message": f"未找到里程碑: {milestone_id}", "formatted_output": f"错误: 未找到里程碑: {milestone_id}"}

    milestone_name = milestone.get("name", "未命名里程碑")

    # 执行删除操作
    result = service.delete_milestone(roadmap_id, milestone_id)

    if not result or result.get("success") is not True:
        error_msg = result.get("error", "未知错误") if result else "删除里程碑失败"
        return {"status": "error", "message": error_msg, "formatted_output": f"错误: {error_msg}"}

    # 格式化输出
    if format_type == "json":
        return {"status": "success", "data": result, "formatted_output": json.dumps(result, indent=2, ensure_ascii=False)}

    # 对于text和table格式，返回相同的简单消息
    return {"status": "success", "data": result, "formatted_output": f"里程碑 '{milestone_name}' (ID: {milestone_id}) 已删除"}


def _list_milestones(service: RoadmapService, args: Dict) -> Dict:
    """
    列出路线图的所有里程碑

    参数:
        service: 路线图服务实例
        args: 命令参数

    返回:
        操作结果字典
    """
    # 获取必要参数
    roadmap_id = args.get("roadmap_id")
    format_type = args.get("format", "table")

    # 首先检查是否有提供路线图ID，如果没有则尝试使用当前活动路线图
    if not roadmap_id:
        roadmap_id = service.active_roadmap_id

        # 如果依然没有路线图ID，提供友好提示
        if not roadmap_id:
            message = """[yellow]当前未指定路线图ID，且未设置活动路线图[/yellow]

可以通过以下命令操作:
[blue]1. 查看所有可用路线图:[/blue]
   roadmap list --all

[blue]2. 切换到活动路线图:[/blue]
   roadmap switch <roadmap_id>

[blue]3. 指定路线图ID执行里程碑命令:[/blue]
   milestone list --roadmap-id=<roadmap_id>"""

            return {"status": "success", "message": "未指定路线图ID，且未设置活动路线图", "formatted_output": message}  # 改为success而非error

    # 获取路线图信息
    roadmap = service.get_roadmap(roadmap_id)

    if not roadmap:
        return {"status": "error", "message": f"未找到路线图: {roadmap_id}", "formatted_output": f"错误: 未找到路线图: {roadmap_id}"}

    # 获取里程碑列表
    milestones = service.list_milestones(roadmap_id)

    # 格式化输出
    if format_type == "json":
        return {"status": "success", "data": {"milestones": milestones}, "formatted_output": json.dumps(milestones, indent=2, ensure_ascii=False)}

    if format_type == "text":
        if not milestones:
            return {"status": "success", "data": {"milestones": []}, "formatted_output": f"路线图 '{roadmap.get('name')}' ({roadmap_id}) 中没有里程碑"}

        output = [f"路线图 '{roadmap.get('name')}' ({roadmap_id}) 中的里程碑:"]

        for milestone in milestones:
            milestone_id = milestone.get("id", "未知ID")
            milestone_name = milestone.get("name", "未命名里程碑")
            milestone_status = milestone.get("status", "未设置状态")
            milestone_due_date = milestone.get("due_date", "未设置截止日期")

            output.append(f"{milestone_id}: {milestone_name} [状态: {milestone_status}] [截止日期: {milestone_due_date}]")

        return {"status": "success", "data": {"milestones": milestones}, "formatted_output": "\n".join(output)}

    # 默认表格格式
    if not milestones:
        return {"status": "success", "data": {"milestones": []}, "formatted_output": f"# 里程碑列表\n\n路线图 '{roadmap.get('name')}' ({roadmap_id}) 中没有里程碑"}

    output = [f"# 路线图 '{roadmap.get('name')}' ({roadmap_id}) 里程碑列表", "", "| ID | 名称 | 状态 | 截止日期 | 任务数量 |", "| --- | --- | --- | --- | --- |"]

    for milestone in milestones:
        milestone_id = milestone.get("id", "未知ID")
        milestone_name = milestone.get("name", "未命名里程碑")
        milestone_status = milestone.get("status", "未设置")
        milestone_due_date = milestone.get("due_date", "未设置")
        task_count = len(milestone.get("tasks", []))

        output.append(f"| {milestone_id} | {milestone_name} | {milestone_status} | " f"{milestone_due_date} | {task_count} |")

    return {"status": "success", "data": {"milestones": milestones}, "formatted_output": "\n".join(output)}


def _get_milestone(service: RoadmapService, args: Dict) -> Dict:
    """
    获取里程碑详细信息

    参数:
        service: 路线图服务实例
        args: 命令参数

    返回:
        操作结果字典
    """
    # 获取必要参数
    roadmap_id = args.get("roadmap_id")
    milestone_id = args.get("milestone_id")
    format_type = args.get("format", "table")

    # 首先检查是否有提供路线图ID，如果没有则尝试使用当前活动路线图
    if not roadmap_id:
        roadmap_id = service.active_roadmap_id

        # 如果依然没有路线图ID，提供友好提示
        if not roadmap_id:
            message = """[yellow]当前未指定路线图ID，且未设置活动路线图[/yellow]

可以通过以下命令操作:
[blue]1. 查看所有可用路线图:[/blue]
   roadmap list --all

[blue]2. 切换到活动路线图:[/blue]
   roadmap switch <roadmap_id>

[blue]3. 指定路线图ID执行里程碑命令:[/blue]
   milestone get --roadmap-id=<roadmap_id> --milestone-id=<milestone_id>"""

            return {"status": "success", "message": "未指定路线图ID，且未设置活动路线图", "formatted_output": message}  # 改为success而非error

    # 检查是否提供了里程碑ID
    if not milestone_id:
        # 如果没有提供里程碑ID，但有路线图ID，则列出该路线图下的所有里程碑
        return _list_milestones(service, {"roadmap_id": roadmap_id, "format": format_type})

    # 获取里程碑
    result = service.get_milestone(roadmap_id, milestone_id)

    if not result or "error" in result:
        error_msg = result.get("error", "未知错误") if result else "获取里程碑失败"
        return {"status": "error", "message": error_msg, "formatted_output": f"错误: {error_msg}"}

    # 格式化输出
    if format_type == "json":
        return {"status": "success", "data": result, "formatted_output": json.dumps(result, indent=2, ensure_ascii=False)}

    if format_type == "text":
        milestone = result.get("milestone", {})
        tasks = result.get("tasks", [])

        milestone_name = milestone.get("name", "未命名里程碑")
        milestone_desc = milestone.get("description", "无描述")
        milestone_status = milestone.get("status", "未知")
        milestone_due_date = milestone.get("due_date", "未设置")

        formatted_text = f"""里程碑: {milestone_name} (ID: {milestone_id})
描述: {milestone_desc}
状态: {milestone_status}
截止日期: {milestone_due_date}

关联任务:
"""
        if tasks:
            for task in tasks:
                task_id = task.get("id", "未知ID")
                task_name = task.get("name", "未命名任务")
                task_status = task.get("status", "未知")
                formatted_text += f"- {task_name} (ID: {task_id}, 状态: {task_status})\n"
        else:
            formatted_text += "- 无关联任务\n"

        return {"status": "success", "data": result, "formatted_output": formatted_text}

    # 默认表格格式
    return {"status": "success", "data": result, "formatted_output": _format_milestone_detail_table(result)}


def _format_milestone_table(milestone: Dict, roadmap_id: str) -> str:
    """
    格式化单个里程碑为表格输出

    参数:
        milestone: 里程碑数据
        roadmap_id: 路线图ID

    返回:
        格式化的表格字符串
    """
    milestone_id = milestone.get("id", "未知ID")
    milestone_name = milestone.get("name", "未命名里程碑")
    milestone_description = milestone.get("description", "")
    milestone_status = milestone.get("status", "未设置")
    milestone_due_date = milestone.get("due_date", "未设置")
    task_count = len(milestone.get("tasks", []))

    output = [
        f"# 里程碑: {milestone_name}",
        "",
        "| 字段 | 值 |",
        "| --- | --- |",
        f"| ID | {milestone_id} |",
        f"| 名称 | {milestone_name} |",
        f"| 描述 | {milestone_description} |",
        f"| 状态 | {milestone_status} |",
        f"| 截止日期 | {milestone_due_date} |",
        f"| 任务数量 | {task_count} |",
        f"| 路线图ID | {roadmap_id} |",
    ]

    return "\n".join(output)


def _format_milestone_detail(milestone: Dict, roadmap_id: str) -> str:
    """
    格式化里程碑详细信息为表格输出，包括任务列表

    参数:
        milestone: 里程碑数据
        roadmap_id: 路线图ID

    返回:
        格式化的表格字符串
    """
    milestone_id = milestone.get("id", "未知ID")
    milestone_name = milestone.get("name", "未命名里程碑")
    milestone_description = milestone.get("description", "")
    milestone_status = milestone.get("status", "未设置")
    milestone_due_date = milestone.get("due_date", "未设置")
    tasks = milestone.get("tasks", [])

    output = [
        f"# 里程碑详情: {milestone_name}",
        "",
        "## 基本信息",
        "| 字段 | 值 |",
        "| --- | --- |",
        f"| ID | {milestone_id} |",
        f"| 名称 | {milestone_name} |",
        f"| 描述 | {milestone_description} |",
        f"| 状态 | {milestone_status} |",
        f"| 截止日期 | {milestone_due_date} |",
        f"| 任务数量 | {len(tasks)} |",
        f"| 路线图ID | {roadmap_id} |",
    ]

    # 添加任务列表
    if tasks:
        output.extend(["", "## 关联任务", "| ID | 任务名称 | 状态 | 优先级 | 负责人 | 截止日期 |", "| --- | --- | --- | --- | --- | --- |"])

        for task in tasks:
            task_id = task.get("id", "未知ID")
            task_name = task.get("name", "未命名任务")
            task_status = task.get("status", "未设置")
            task_priority = task.get("priority", "未设置")
            assignee = task.get("assignee", "未分配")
            due_date = task.get("due_date", "未设置")

            output.append(f"| {task_id} | {task_name} | {task_status} | {task_priority} | " f"{assignee} | {due_date} |")
    else:
        output.extend(["", "## 关联任务", "此里程碑暂无关联任务"])

    return "\n".join(output)


def _format_milestone_detail_table(result: Dict) -> str:
    """
    格式化里程碑详细信息为表格输出，包括任务列表

    参数:
        result: 获取里程碑详细信息的结果字典

    返回:
        格式化的表格字符串
    """
    milestone = result.get("milestone", {})
    tasks = result.get("tasks", [])

    milestone_name = milestone.get("name", "未命名里程碑")
    milestone_desc = milestone.get("description", "无描述")
    milestone_status = milestone.get("status", "未知")
    milestone_due_date = milestone.get("due_date", "未设置")

    formatted_text = f"""里程碑: {milestone_name} (ID: {result.get("id")})
描述: {milestone_desc}
状态: {milestone_status}
截止日期: {milestone_due_date}

关联任务:
"""
    if tasks:
        for task in tasks:
            task_id = task.get("id", "未知ID")
            task_name = task.get("name", "未命名任务")
            task_status = task.get("status", "未知")
            formatted_text += f"- {task_name} (ID: {task_id}, 状态: {task_status})\n"
    else:
        formatted_text += "- 无关联任务\n"

    return formatted_text
