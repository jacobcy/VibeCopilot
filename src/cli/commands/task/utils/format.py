"""
任务输出格式化工具模块
"""

import json
from typing import Any, Dict, List

import yaml
from rich.table import Table


def format_task_output(task_data: Dict[str, Any], format: str = "yaml", verbose: bool = False) -> str:
    """格式化任务输出

    Args:
        task_data: 任务数据字典
        format: 输出格式，支持 yaml 和 json
        verbose: 是否显示详细信息

    Returns:
        格式化后的字符串
    """
    if not task_data:
        return ""

    # 如果不需要详细信息，移除一些字段
    if not verbose:
        task_data = {k: v for k, v in task_data.items() if k in ["id", "title", "status", "assignee", "story_id", "created_at"]}

    if format.lower() == "json":
        return json.dumps(task_data, ensure_ascii=False, indent=2)
    else:  # 默认使用YAML
        return yaml.safe_dump(task_data, allow_unicode=True, sort_keys=False)


def format_task_table(task_data: Dict[str, Any], verbose: bool = False) -> Table:
    """生成任务信息表格

    Args:
        task_data: 任务数据字典
        verbose: 是否显示详细信息

    Returns:
        Rich Table 对象
    """
    table = Table(title="任务详情")

    # 添加基本列
    table.add_column("字段", style="bold cyan", width=20)
    table.add_column("值", style="white")

    # 添加基本信息
    basic_fields = [
        ("ID", "id"),
        ("标题", "title"),
        ("状态", "status"),
        ("负责人", "assignee"),
        ("创建时间", "created_at"),
        ("Story ID", "story_id"),
    ]

    for display_name, field_name in basic_fields:
        value = str(task_data.get(field_name, "-"))
        table.add_row(display_name, value)

    # 如果需要详细信息，添加更多字段
    if verbose:
        detail_fields = [
            ("描述", "description"),
            ("标签", "labels"),
            ("优先级", "priority"),
            ("截止日期", "due_date"),
            ("更新时间", "updated_at"),
            ("Memory链接", "memory_link"),
            ("GitHub Issue", "github_issue"),
            ("工作流会话", "flow_session_id"),
        ]

        for display_name, field_name in detail_fields:
            value = task_data.get(field_name)
            if value:
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False, indent=2)
                table.add_row(display_name, str(value))

    return table


def format_task_list_table(tasks: List[Dict[str, Any]], verbose: bool = False) -> Table:
    """生成任务列表表格

    Args:
        tasks: 任务数据字典列表
        verbose: 是否显示详细信息

    Returns:
        Rich Table 对象
    """
    table = Table(title="任务列表")

    # 添加基本列
    table.add_column("ID", style="dim", width=12)
    table.add_column("标题", style="bold cyan")
    table.add_column("状态", style="magenta")
    table.add_column("负责人", style="green")

    if verbose:
        table.add_column("类型", style="dim")
        table.add_column("关联 Story", style="dim")
        table.add_column("创建时间", style="dim")

    # 添加任务行
    for task in tasks:
        row = [
            task.get("id", "")[:8] + "..." if not verbose else task.get("id", ""),
            task.get("title", ""),
            task.get("status", ""),
            task.get("assignee", "-"),
        ]

        if verbose:
            # 添加任务类型
            task_type = "临时任务" if not task.get("story_id") else "正式任务"
            row.append(task_type)
            # 关联Story
            row.append(task.get("story_id", "-"))
            # 创建时间
            created_time = task.get("created_at", "-")
            if created_time != "-":
                if hasattr(created_time, "strftime"):
                    created_time = created_time.strftime("%Y-%m-%d %H:%M")
                else:
                    created_time = str(created_time)
            row.append(created_time)

        table.add_row(*row)

    return table
