"""
命令处理模块 - 管理路线图任务依赖关系操作

此模块实现路线图任务依赖关系的命令处理逻辑，包括添加、删除和查看依赖关系的功能
"""

import json
from typing import Any, Dict, List, Optional

from src.roadmap.service import RoadmapService


def handle_dependency_command(args, roadmap_service: RoadmapService = None):
    """
    处理任务依赖关系相关命令

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

    if sub_command == "add":
        return _add_dependency(roadmap_service, args)
    elif sub_command == "remove":
        return _remove_dependency(roadmap_service, args)
    elif sub_command == "list":
        return _list_dependencies(roadmap_service, args)
    else:
        return {
            "status": "error",
            "message": f"未知的依赖关系命令: {sub_command}",
            "formatted_output": f"错误: 未知的依赖关系命令: {sub_command}\n可用命令: add, remove, list",
        }


def _add_dependency(service: RoadmapService, args: Dict) -> Dict:
    """
    添加任务依赖关系

    参数:
        service: 路线图服务实例
        args: 命令参数

    返回:
        操作结果字典
    """
    # 获取必要参数
    roadmap_id = args.get("roadmap_id")
    task_id = args.get("task_id")
    depends_on_id = args.get("depends_on_id")
    format_type = args.get("format", "table")

    # 验证必要参数
    if not roadmap_id:
        # 尝试获取当前激活的路线图ID
        active_roadmap = service.get_active_roadmap()
        if active_roadmap:
            roadmap_id = active_roadmap.get("id")
        else:
            # 提供友好的提示信息，而不是错误
            return {
                "status": "success",
                "message": "未指定路线图ID且无激活路线图",
                "formatted_output": "\033[33m提示: 未指定路线图ID且当前没有激活的路线图\033[0m\n\n"
                "您可以通过以下方式继续:\n"
                "1. 使用 `/roadmap list` 查看可用的路线图\n"
                "2. 使用 `/roadmap show <roadmap_id>` 指定要操作的路线图\n"
                "3. 使用 `/roadmap switch <roadmap_id>` 切换到一个活动路线图\n"
                "4. 使用 `--roadmap=<roadmap_id>` 参数指定路线图ID",
            }

    if not task_id:
        return {"status": "error", "message": "缺少任务ID", "formatted_output": "错误: 请提供需要添加依赖的任务ID"}

    if not depends_on_id:
        return {"status": "error", "message": "缺少依赖任务ID", "formatted_output": "错误: 请提供被依赖的任务ID"}

    # 添加依赖关系
    result = service.add_task_dependency(roadmap_id, task_id, depends_on_id)

    if not result or "error" in result:
        error_msg = result.get("error", "未知错误") if result else "添加依赖关系失败"
        return {"status": "error", "message": error_msg, "formatted_output": f"错误: {error_msg}"}

    # 格式化输出
    if format_type == "json":
        return {"status": "success", "data": result, "formatted_output": json.dumps(result, indent=2, ensure_ascii=False)}

    # 为text和table格式提供简单的成功消息
    task_name = result.get("task", {}).get("name", task_id)
    depends_on_name = result.get("depends_on", {}).get("name", depends_on_id)

    return {"status": "success", "data": result, "formatted_output": f"已成功添加依赖关系: 任务 '{task_name}' 现在依赖于 '{depends_on_name}'"}


def _remove_dependency(service: RoadmapService, args: Dict) -> Dict:
    """
    删除任务依赖关系

    参数:
        service: 路线图服务实例
        args: 命令参数

    返回:
        操作结果字典
    """
    # 获取必要参数
    roadmap_id = args.get("roadmap_id")
    task_id = args.get("task_id")
    depends_on_id = args.get("depends_on_id")
    format_type = args.get("format", "table")

    # 验证必要参数
    if not roadmap_id:
        # 尝试获取当前激活的路线图ID
        active_roadmap = service.get_active_roadmap()
        if active_roadmap:
            roadmap_id = active_roadmap.get("id")
        else:
            # 提供友好的提示信息，而不是错误
            return {
                "status": "success",
                "message": "未指定路线图ID且无激活路线图",
                "formatted_output": "\033[33m提示: 未指定路线图ID且当前没有激活的路线图\033[0m\n\n"
                "您可以通过以下方式继续:\n"
                "1. 使用 `/roadmap list` 查看可用的路线图\n"
                "2. 使用 `/roadmap show <roadmap_id>` 指定要操作的路线图\n"
                "3. 使用 `/roadmap switch <roadmap_id>` 切换到一个活动路线图\n"
                "4. 使用 `--roadmap=<roadmap_id>` 参数指定路线图ID",
            }

    if not task_id:
        return {"status": "error", "message": "缺少任务ID", "formatted_output": "错误: 请提供需要移除依赖的任务ID"}

    if not depends_on_id:
        return {"status": "error", "message": "缺少依赖任务ID", "formatted_output": "错误: 请提供被依赖的任务ID"}

    # 获取任务信息，用于显示
    task = service.get_task(roadmap_id, task_id)
    depends_on_task = service.get_task(roadmap_id, depends_on_id)

    if not task:
        return {"status": "error", "message": f"未找到任务: {task_id}", "formatted_output": f"错误: 未找到任务: {task_id}"}

    if not depends_on_task:
        return {"status": "error", "message": f"未找到依赖任务: {depends_on_id}", "formatted_output": f"错误: 未找到依赖任务: {depends_on_id}"}

    task_name = task.get("name", task_id)
    depends_on_name = depends_on_task.get("name", depends_on_id)

    # 删除依赖关系
    result = service.remove_task_dependency(roadmap_id, task_id, depends_on_id)

    if not result or result.get("success") is not True:
        error_msg = result.get("error", "未知错误") if result else "删除依赖关系失败"
        return {"status": "error", "message": error_msg, "formatted_output": f"错误: {error_msg}"}

    # 格式化输出
    if format_type == "json":
        return {"status": "success", "data": result, "formatted_output": json.dumps(result, indent=2, ensure_ascii=False)}

    # 为text和table格式提供简单的成功消息
    return {"status": "success", "data": result, "formatted_output": f"已成功移除依赖关系: 任务 '{task_name}' 不再依赖于 '{depends_on_name}'"}


def _list_dependencies(service: RoadmapService, args: Dict) -> Dict:
    """
    列出任务的依赖关系

    参数:
        service: 路线图服务实例
        args: 命令参数

    返回:
        操作结果字典
    """
    # 获取必要参数
    roadmap_id = args.get("roadmap_id")
    task_id = args.get("task_id")
    format_type = args.get("format", "table")
    direction = args.get("direction", "both").lower()  # both, incoming, outgoing

    # 验证必要参数
    if not roadmap_id:
        # 尝试获取当前激活的路线图ID
        active_roadmap = service.get_active_roadmap()
        if active_roadmap:
            roadmap_id = active_roadmap.get("id")
        else:
            # 提供友好的提示信息，而不是错误
            return {
                "status": "success",
                "message": "未指定路线图ID且无激活路线图",
                "formatted_output": "\033[33m提示: 未指定路线图ID且当前没有激活的路线图\033[0m\n\n"
                "您可以通过以下方式继续:\n"
                "1. 使用 `/roadmap list` 查看可用的路线图\n"
                "2. 使用 `/roadmap show <roadmap_id>` 指定要操作的路线图\n"
                "3. 使用 `/roadmap switch <roadmap_id>` 切换到一个活动路线图\n"
                "4. 使用 `--roadmap=<roadmap_id>` 参数指定路线图ID",
            }

    if not task_id:
        return {"status": "error", "message": "缺少任务ID", "formatted_output": "错误: 请提供任务ID"}

    # 验证方向参数
    if direction not in ["both", "incoming", "outgoing"]:
        return {
            "status": "error",
            "message": f"无效的依赖方向: {direction}",
            "formatted_output": f"错误: 无效的依赖方向: {direction}\n可用选项: both, incoming, outgoing",
        }

    # 获取任务信息
    task = service.get_task(roadmap_id, task_id)

    if not task:
        return {"status": "error", "message": f"未找到任务: {task_id}", "formatted_output": f"错误: 未找到任务: {task_id}"}

    # 获取依赖关系
    result = service.get_task_dependencies(roadmap_id, task_id, direction)

    if not result or "error" in result:
        error_msg = result.get("error", "未知错误") if result else "获取依赖关系失败"
        return {"status": "error", "message": error_msg, "formatted_output": f"错误: {error_msg}"}

    # 解析依赖关系数据
    task_name = task.get("name", "未命名任务")
    incoming = result.get("incoming", [])
    outgoing = result.get("outgoing", [])

    # 格式化输出
    if format_type == "json":
        return {"status": "success", "data": result, "formatted_output": json.dumps(result, indent=2, ensure_ascii=False)}

    if format_type == "text":
        output = [f"任务 '{task_name}' (ID: {task_id}) 的依赖关系:"]

        if direction in ["both", "incoming"] and incoming:
            output.append("\n前置依赖 (此任务依赖于):")
            for dep in incoming:
                dep_id = dep.get("id", "未知ID")
                dep_name = dep.get("name", "未命名任务")
                dep_status = dep.get("status", "未设置状态")
                output.append(f"  - {dep_id}: {dep_name} [状态: {dep_status}]")
        elif direction in ["both", "incoming"]:
            output.append("\n前置依赖: 无")

        if direction in ["both", "outgoing"] and outgoing:
            output.append("\n后置依赖 (依赖于此任务):")
            for dep in outgoing:
                dep_id = dep.get("id", "未知ID")
                dep_name = dep.get("name", "未命名任务")
                dep_status = dep.get("status", "未设置状态")
                output.append(f"  - {dep_id}: {dep_name} [状态: {dep_status}]")
        elif direction in ["both", "outgoing"]:
            output.append("\n后置依赖: 无")

        return {"status": "success", "data": result, "formatted_output": "\n".join(output)}

    # 默认表格格式
    output = [f"# 任务 '{task_name}' (ID: {task_id}) 依赖关系"]

    if direction in ["both", "incoming"]:
        output.extend(["", "## 前置依赖 (此任务依赖于)"])

        if incoming:
            output.extend(["| ID | 任务名称 | 状态 | 优先级 | 负责人 |", "| --- | --- | --- | --- | --- |"])

            for dep in incoming:
                dep_id = dep.get("id", "未知ID")
                dep_name = dep.get("name", "未命名任务")
                dep_status = dep.get("status", "未设置")
                dep_priority = dep.get("priority", "未设置")
                dep_assignee = dep.get("assignee", "未分配")

                output.append(f"| {dep_id} | {dep_name} | {dep_status} | {dep_priority} | {dep_assignee} |")
        else:
            output.append("此任务没有前置依赖")

    if direction in ["both", "outgoing"]:
        output.extend(["", "## 后置依赖 (依赖于此任务)"])

        if outgoing:
            output.extend(["| ID | 任务名称 | 状态 | 优先级 | 负责人 |", "| --- | --- | --- | --- | --- |"])

            for dep in outgoing:
                dep_id = dep.get("id", "未知ID")
                dep_name = dep.get("name", "未命名任务")
                dep_status = dep.get("status", "未设置")
                dep_priority = dep.get("priority", "未设置")
                dep_assignee = dep.get("assignee", "未分配")

                output.append(f"| {dep_id} | {dep_name} | {dep_status} | {dep_priority} | {dep_assignee} |")
        else:
            output.append("没有任务依赖于此任务")

    return {"status": "success", "data": result, "formatted_output": "\n".join(output)}
