"""
命令处理模块 - 管理路线图任务相关操作

此模块实现路线图任务管理的命令处理逻辑，包括创建、更新、删除和查看任务
"""

import json
from typing import Any, Dict, List, Optional

from src.roadmap.service import RoadmapService


def handle_task_command(args: Dict) -> Dict:
    """
    处理路线图任务命令

    参数:
        args: 命令参数字典

    返回:
        命令执行结果字典
    """
    service = RoadmapService()

    # 获取或设置路线图ID
    roadmap_id = args.get("roadmap_id")
    if not roadmap_id:
        active_roadmap = service.get_active_roadmap()
        if active_roadmap:
            roadmap_id = active_roadmap.get("id")
        else:
            # 如果没有指定路线图ID且没有活动路线图，返回友好提示
            return {
                "status": "success",
                "message": "需要指定路线图ID或设置活动路线图",
                "formatted_output": "提示：要使用任务命令，您需要执行以下操作之一：\n"
                "1. 使用 `/roadmap list` 查看可用路线图\n"
                "2. 使用 `/roadmap task --roadmap-id <id>` 指定路线图ID\n"
                "3. 使用 `/roadmap switch <id>` 切换到一个活动路线图",
            }

    # 获取子命令和相关参数
    subcommand = args.get("subcommand", "list")
    task_id = args.get("task_id")
    milestone_id = args.get("milestone_id")
    format = args.get("format", "table")

    # 处理各种子命令
    if subcommand == "create":
        return _create_task(service, roadmap_id, args, format)
    elif subcommand == "update":
        return _update_task(service, roadmap_id, task_id, args, format)
    elif subcommand == "delete":
        return _delete_task(service, roadmap_id, task_id, format)
    elif subcommand == "show" and task_id:
        return _show_task_detail(service, roadmap_id, task_id, format)
    elif subcommand == "list" or subcommand == "show":
        return _list_tasks(service, roadmap_id, milestone_id, format)
    else:
        return {"status": "error", "message": f"未知的子命令: {subcommand}", "formatted_output": f"错误: 未知的子命令: {subcommand}"}


def _create_task(service: RoadmapService, roadmap_id: str, args: Dict, format: str) -> Dict:
    """
    创建新的任务

    参数:
        service: 路线图服务实例
        roadmap_id: 路线图ID
        args: 命令参数
        format: 输出格式

    返回:
        操作结果字典
    """
    # 确保有里程碑ID
    if not milestone_id:
        return {"status": "error", "message": "缺少里程碑ID", "formatted_output": "错误: 请指定任务所属的里程碑ID"}

    # 从参数中提取任务信息
    task_data = {
        "name": args.get("name"),
        "description": args.get("description", ""),
        "milestone_id": milestone_id,
        "status": args.get("status", "not_started"),
        "priority": args.get("priority", "medium"),
        "assignee": args.get("assignee", ""),
        "tags": args.get("tags", []),
    }

    # 处理标签
    if isinstance(task_data["tags"], str):
        task_data["tags"] = [tag.strip() for tag in task_data["tags"].split(",") if tag.strip()]

    # 验证必要字段
    if not task_data["name"]:
        return {"status": "error", "message": "缺少任务名称", "formatted_output": "错误: 请提供任务名称"}

    # 创建任务
    result = service.create_task(roadmap_id, task_data)

    if not result or "id" not in result:
        return {"status": "error", "message": "创建任务失败", "formatted_output": "错误: 创建任务失败，请检查参数或路线图/里程碑ID是否正确"}

    # 根据格式返回结果
    if format == "json":
        return {"status": "success", "data": {"task": result}, "formatted_output": json.dumps(result, indent=2, ensure_ascii=False)}

    if format == "text":
        tags_str = ", ".join(result.get("tags", [])) if result.get("tags") else ""
        output = [
            f"任务创建成功: {result.get('name')} ({result.get('id')})",
            f"描述: {result.get('description', '')}",
            f"所属里程碑: {result.get('milestone_id', '')}",
            f"状态: {result.get('status', '')}",
            f"优先级: {result.get('priority', '')}",
            f"负责人: {result.get('assignee', '')}",
            f"标签: {tags_str}",
        ]
        return {"status": "success", "data": {"task": result}, "formatted_output": "\n".join(output)}

    # 默认表格格式
    tags_str = ", ".join(result.get("tags", [])) if result.get("tags") else ""
    output = [
        f"# 任务创建成功: {result.get('name')} ({result.get('id')})",
        "\n## 基本信息",
        "| 属性 | 值 |",
        "| --- | --- |",
        f"| ID | {result.get('id')} |",
        f"| 描述 | {result.get('description', '')} |",
        f"| 所属里程碑 | {result.get('milestone_id', '')} |",
        f"| 状态 | {result.get('status', '')} |",
        f"| 优先级 | {result.get('priority', '')} |",
        f"| 负责人 | {result.get('assignee', '')} |",
        f"| 标签 | {tags_str} |",
    ]

    return {"status": "success", "data": {"task": result}, "formatted_output": "\n".join(output)}


def _update_task(service: RoadmapService, roadmap_id: str, task_id: str, args: Dict, format: str) -> Dict:
    """
    更新任务信息

    参数:
        service: 路线图服务实例
        roadmap_id: 路线图ID
        task_id: 任务ID
        args: 命令参数
        format: 输出格式

    返回:
        操作结果字典
    """
    # 确保有任务ID
    if not task_id:
        return {"status": "error", "message": "缺少任务ID", "formatted_output": "错误: 请指定要更新的任务ID"}

    # 从参数中提取需要更新的字段
    update_data = {}
    if "name" in args and args["name"]:
        update_data["name"] = args["name"]
    if "description" in args:
        update_data["description"] = args["description"]
    if "milestone_id" in args and args["milestone_id"]:
        update_data["milestone_id"] = args["milestone_id"]
    if "status" in args:
        update_data["status"] = args["status"]
    if "priority" in args:
        update_data["priority"] = args["priority"]
    if "assignee" in args:
        update_data["assignee"] = args["assignee"]
    if "tags" in args:
        if isinstance(args["tags"], str):
            update_data["tags"] = [tag.strip() for tag in args["tags"].split(",") if tag.strip()]
        else:
            update_data["tags"] = args["tags"]

    # 如果没有提供任何更新字段
    if not update_data:
        return {"status": "error", "message": "未提供任何更新字段", "formatted_output": "错误: 请提供至少一个要更新的字段"}

    # 更新任务
    result = service.update_task(roadmap_id, task_id, update_data)

    if not result:
        return {"status": "error", "message": f"更新任务失败: {task_id}", "formatted_output": f"错误: 更新任务失败，请检查任务ID是否正确"}

    # 根据格式返回结果
    if format == "json":
        return {"status": "success", "data": {"task": result}, "formatted_output": json.dumps(result, indent=2, ensure_ascii=False)}

    if format == "text":
        tags_str = ", ".join(result.get("tags", [])) if result.get("tags") else ""
        output = [
            f"任务更新成功: {result.get('name')} ({task_id})",
            f"描述: {result.get('description', '')}",
            f"所属里程碑: {result.get('milestone_id', '')}",
            f"状态: {result.get('status', '')}",
            f"优先级: {result.get('priority', '')}",
            f"负责人: {result.get('assignee', '')}",
            f"标签: {tags_str}",
        ]
        return {"status": "success", "data": {"task": result}, "formatted_output": "\n".join(output)}

    # 默认表格格式
    tags_str = ", ".join(result.get("tags", [])) if result.get("tags") else ""
    output = [
        f"# 任务更新成功: {result.get('name')} ({task_id})",
        "\n## 基本信息",
        "| 属性 | 值 |",
        "| --- | --- |",
        f"| ID | {task_id} |",
        f"| 描述 | {result.get('description', '')} |",
        f"| 所属里程碑 | {result.get('milestone_id', '')} |",
        f"| 状态 | {result.get('status', '')} |",
        f"| 优先级 | {result.get('priority', '')} |",
        f"| 负责人 | {result.get('assignee', '')} |",
        f"| 标签 | {tags_str} |",
    ]

    return {"status": "success", "data": {"task": result}, "formatted_output": "\n".join(output)}


def _delete_task(service: RoadmapService, roadmap_id: str, task_id: str, format: str) -> Dict:
    """
    删除任务

    参数:
        service: 路线图服务实例
        roadmap_id: 路线图ID
        task_id: 任务ID
        format: 输出格式

    返回:
        操作结果字典
    """
    # 确保有任务ID
    if not task_id:
        return {"status": "error", "message": "缺少任务ID", "formatted_output": "错误: 请指定要删除的任务ID"}

    # 删除任务
    result = service.delete_task(roadmap_id, task_id)

    if not result:
        return {"status": "error", "message": f"删除任务失败: {task_id}", "formatted_output": f"错误: 删除任务失败，请检查任务ID是否正确"}

    # 根据格式返回结果
    message = f"任务删除成功: {task_id}"

    if format == "json":
        return {
            "status": "success",
            "data": {"task_id": task_id},
            "formatted_output": json.dumps({"task_id": task_id, "message": message}, indent=2, ensure_ascii=False),
        }

    if format == "text":
        return {"status": "success", "data": {"task_id": task_id}, "formatted_output": message}

    # 默认表格格式
    output = ["# 操作结果", "| 操作 | 状态 | 详情 |", "| --- | --- | --- |", f"| 删除任务 | 成功 | ID: {task_id} |"]

    return {"status": "success", "data": {"task_id": task_id}, "formatted_output": "\n".join(output)}


def _list_tasks(service: RoadmapService, roadmap_id: str, milestone_id: str, format: str) -> Dict:
    """
    列出路线图或特定里程碑的所有任务

    参数:
        service: 路线图服务实例
        roadmap_id: 路线图ID
        milestone_id: 里程碑ID (可选)
        format: 输出格式

    返回:
        操作结果字典
    """
    # 获取路线图详情确认存在
    roadmap = service.get_roadmap(roadmap_id)

    if not roadmap:
        return {"status": "error", "message": f"未找到路线图: {roadmap_id}", "formatted_output": f"错误: 未找到路线图: {roadmap_id}"}

    # 提取任务列表（可能按里程碑过滤）
    tasks = service.get_tasks(roadmap_id, milestone_id)

    milestone_name = ""
    if milestone_id:
        milestone = service.get_milestone(roadmap_id, milestone_id)
        if milestone:
            milestone_name = milestone.get("name", "")

    # 根据格式返回结果
    if format == "json":
        return {"status": "success", "data": {"tasks": tasks}, "formatted_output": json.dumps(tasks, indent=2, ensure_ascii=False)}

    if format == "text":
        if not tasks:
            if milestone_id:
                return {"status": "success", "data": {"tasks": []}, "formatted_output": f"里程碑 {milestone_id} 没有任务"}
            else:
                return {"status": "success", "data": {"tasks": []}, "formatted_output": f"路线图 {roadmap_id} 没有任务"}

        if milestone_id:
            output = [f"里程碑 '{milestone_name}' ({milestone_id}) 的任务:"]
        else:
            output = [f"路线图 '{roadmap.get('name')}' ({roadmap_id}) 的所有任务:"]

        for task in tasks:
            tags_str = ", ".join(task.get("tags", [])) if task.get("tags") else ""
            output.append(
                f"{task.get('id')}: {task.get('name')} - "
                f"状态: {task.get('status', '未知')}, "
                f"优先级: {task.get('priority', '中')}, "
                f"负责人: {task.get('assignee', '未分配')}"
            )

        return {"status": "success", "data": {"tasks": tasks}, "formatted_output": "\n".join(output)}

    # 默认表格格式
    if not tasks:
        if milestone_id:
            return {"status": "success", "data": {"tasks": []}, "formatted_output": f"# 里程碑 '{milestone_name}' ({milestone_id}) 没有任务"}
        else:
            return {"status": "success", "data": {"tasks": []}, "formatted_output": f"# 路线图 '{roadmap.get('name')}' ({roadmap_id}) 没有任务"}

    if milestone_id:
        output = [f"# 里程碑 '{milestone_name}' ({milestone_id}) 的任务"]
    else:
        output = [f"# 路线图 '{roadmap.get('name')}' ({roadmap_id}) 的所有任务"]

    output.extend(["", "| ID | 名称 | 状态 | 优先级 | 负责人 | 标签 |", "| --- | --- | --- | --- | --- | --- |"])

    for task in tasks:
        tags_str = ", ".join(task.get("tags", [])) if task.get("tags") else ""
        output.append(
            f"| {task.get('id')} | {task.get('name')} | {task.get('status', '未知')} | "
            f"{task.get('priority', '中')} | {task.get('assignee', '未分配')} | {tags_str} |"
        )

    return {"status": "success", "data": {"tasks": tasks}, "formatted_output": "\n".join(output)}


def _show_task_detail(service: RoadmapService, roadmap_id: str, task_id: str, format: str) -> Dict:
    """
    显示任务详情

    参数:
        service: 路线图服务实例
        roadmap_id: 路线图ID
        task_id: 任务ID
        format: 输出格式

    返回:
        操作结果字典
    """
    # 获取任务详情
    task = service.get_task(roadmap_id, task_id)

    if not task:
        return {"status": "error", "message": f"未找到任务: {task_id}", "formatted_output": f"错误: 未找到任务: {task_id}"}

    # 根据格式返回结果
    if format == "json":
        return {"status": "success", "data": {"task": task}, "formatted_output": json.dumps(task, indent=2, ensure_ascii=False)}

    if format == "text":
        tags_str = ", ".join(task.get("tags", [])) if task.get("tags") else ""
        output = [
            f"任务详情: {task.get('name')} ({task.get('id')})",
            f"描述: {task.get('description', '')}",
            f"所属里程碑: {task.get('milestone_id', '')}",
            f"状态: {task.get('status', '')}",
            f"优先级: {task.get('priority', '')}",
            f"负责人: {task.get('assignee', '')}",
            f"标签: {tags_str}",
        ]
        return {"status": "success", "data": {"task": task}, "formatted_output": "\n".join(output)}

    # 默认表格格式
    tags_str = ", ".join(task.get("tags", [])) if task.get("tags") else ""
    output = [
        f"# 任务详情: {task.get('name')} ({task.get('id')})",
        "\n## 基本信息",
        "| 属性 | 值 |",
        "| --- | --- |",
        f"| ID | {task.get('id')} |",
        f"| 描述 | {task.get('description', '')} |",
        f"| 所属里程碑 | {task.get('milestone_id', '')} |",
        f"| 状态 | {task.get('status', '')} |",
        f"| 优先级 | {task.get('priority', '')} |",
        f"| 负责人 | {task.get('assignee', '')} |",
        f"| 标签 | {tags_str} |",
    ]

    return {"status": "success", "data": {"task": task}, "formatted_output": "\n".join(output)}
