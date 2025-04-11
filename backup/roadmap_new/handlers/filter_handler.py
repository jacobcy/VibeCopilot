"""
命令处理模块 - 管理路线图任务筛选相关操作

此模块实现路线图任务筛选的命令处理逻辑，用于根据各种条件筛选和显示任务
"""

import json
from typing import Any, Dict, List, Optional

from src.roadmap.service import RoadmapService


def handle_filter_command(args, roadmap_service: RoadmapService = None):
    """
    处理任务筛选命令

    参数:
        args: 命令参数
        roadmap_service: 路线图服务实例

    返回:
        包含操作结果和格式化输出的字典
    """
    if not roadmap_service:
        roadmap_service = RoadmapService()

    # 获取基本参数
    roadmap_id = args.get("roadmap_id")
    format_type = args.get("format", "table")

    # 确保有路线图ID
    if not roadmap_id:
        return {"status": "error", "message": "缺少路线图ID", "formatted_output": "错误: 请指定路线图ID"}

    # 获取筛选参数
    filter_args = _extract_filter_args(args)

    # 执行筛选操作
    return _filter_tasks(roadmap_service, roadmap_id, filter_args, format_type)


def _extract_filter_args(args: Dict) -> Dict:
    """
    从命令参数中提取筛选条件

    参数:
        args: 命令参数

    返回:
        筛选条件字典
    """
    filter_args = {}

    # 任务状态筛选
    if "status" in args:
        filter_args["status"] = args["status"]

    # 优先级筛选
    if "priority" in args:
        filter_args["priority"] = args["priority"]

    # 标签筛选
    if "tags" in args:
        # 处理标签，确保是列表格式
        tags = args["tags"]
        if isinstance(tags, str):
            # 如果是逗号分隔的字符串，拆分为列表
            filter_args["tags"] = [tag.strip() for tag in tags.split(",")]
        else:
            filter_args["tags"] = tags

    # 里程碑筛选
    if "milestone_id" in args:
        filter_args["milestone_id"] = args["milestone_id"]

    # 负责人筛选
    if "assignee" in args:
        filter_args["assignee"] = args["assignee"]

    # 截止日期筛选
    if "due_before" in args:
        filter_args["due_before"] = args["due_before"]

    if "due_after" in args:
        filter_args["due_after"] = args["due_after"]

    # 文本搜索
    if "search" in args:
        filter_args["search"] = args["search"]

    # 依赖关系筛选
    if "has_dependencies" in args:
        filter_args["has_dependencies"] = args["has_dependencies"]

    # 排序
    if "sort_by" in args:
        filter_args["sort_by"] = args["sort_by"]

    if "sort_order" in args:
        filter_args["sort_order"] = args["sort_order"]

    return filter_args


def _filter_tasks(service: RoadmapService, roadmap_id: str, filter_args: Dict, format: str) -> Dict:
    """
    根据条件筛选任务

    参数:
        service: 路线图服务实例
        roadmap_id: 路线图ID
        filter_args: 筛选条件
        format: 输出格式

    返回:
        操作结果字典
    """
    # 获取路线图详情确认存在
    roadmap = service.get_roadmap(roadmap_id)

    if not roadmap:
        return {"status": "error", "message": f"未找到路线图: {roadmap_id}", "formatted_output": f"错误: 未找到路线图: {roadmap_id}"}

    # 执行筛选操作
    filtered_tasks = service.filter_tasks(roadmap_id, **filter_args)

    # 根据格式返回结果
    if format == "json":
        return {"status": "success", "data": {"tasks": filtered_tasks}, "formatted_output": json.dumps(filtered_tasks, indent=2, ensure_ascii=False)}

    if format == "text":
        if not filtered_tasks:
            return {"status": "success", "data": {"tasks": []}, "formatted_output": "没有找到符合条件的任务"}

        output = [f"路线图 '{roadmap.get('name')}' ({roadmap_id}) 中符合条件的任务:"]

        for task in filtered_tasks:
            task_id = task.get("id", "未知ID")
            task_name = task.get("name", "未命名任务")
            task_status = task.get("status", "未设置状态")

            milestone_name = "未分配"
            if "milestone" in task and task["milestone"]:
                milestone_name = task["milestone"].get("name", "未命名里程碑")

            output.append(f"{task_id}: {task_name} [状态: {task_status}] [里程碑: {milestone_name}]")

        return {"status": "success", "data": {"tasks": filtered_tasks}, "formatted_output": "\n".join(output)}

    # 默认表格格式
    if not filtered_tasks:
        return {"status": "success", "data": {"tasks": []}, "formatted_output": f"# 筛选结果\n\n路线图 '{roadmap.get('name')}' ({roadmap_id}) 中没有找到符合条件的任务"}

    filter_description = _format_filter_description(filter_args)

    output = [f"# 路线图 '{roadmap.get('name')}' ({roadmap_id}) 筛选结果"]

    if filter_description:
        output.extend(["", "## 筛选条件", filter_description, ""])

    output.extend(["", "## 任务列表", "| ID | 任务名称 | 状态 | 优先级 | 里程碑 | 负责人 | 截止日期 |", "| --- | --- | --- | --- | --- | --- | --- |"])

    for task in filtered_tasks:
        task_id = task.get("id", "未知ID")
        task_name = task.get("name", "未命名任务")
        task_status = task.get("status", "未设置")
        task_priority = task.get("priority", "未设置")

        milestone_name = "未分配"
        if "milestone" in task and task["milestone"]:
            milestone_name = task["milestone"].get("name", "未命名里程碑")

        assignee = task.get("assignee", "未分配")
        due_date = task.get("due_date", "未设置")

        output.append(f"| {task_id} | {task_name} | {task_status} | {task_priority} | " f"{milestone_name} | {assignee} | {due_date} |")

    return {"status": "success", "data": {"tasks": filtered_tasks}, "formatted_output": "\n".join(output)}


def _format_filter_description(filter_args: Dict) -> str:
    """
    格式化筛选条件描述

    参数:
        filter_args: 筛选条件

    返回:
        格式化的筛选条件描述
    """
    if not filter_args:
        return ""

    descriptions = []

    # 将筛选条件转换为表格格式
    description = "| 筛选条件 | 值 |\n| --- | --- |"

    for key, value in filter_args.items():
        # 友好的条件名称
        condition_name = {
            "status": "状态",
            "priority": "优先级",
            "tags": "标签",
            "milestone_id": "里程碑ID",
            "assignee": "负责人",
            "due_before": "截止日期早于",
            "due_after": "截止日期晚于",
            "search": "搜索文本",
            "has_dependencies": "有依赖关系",
            "sort_by": "排序字段",
            "sort_order": "排序方向",
        }.get(key, key)

        # 格式化值
        if isinstance(value, list):
            formatted_value = ", ".join(value)
        else:
            formatted_value = str(value)

        description += f"\n| {condition_name} | {formatted_value} |"

    return description
