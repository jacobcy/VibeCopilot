"""
任务输出格式化工具模块
"""

import json
from datetime import date, datetime
from typing import Any, Dict, List, Union

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()


def format_task_output(task_data: Dict[str, Any], format: str = "yaml", verbose: bool = False) -> Union[str, Table]:
    """格式化任务输出

    Args:
        task_data: 任务数据字典
        format: 输出格式，支持 yaml, json, 或 table (默认)
        verbose: 是否显示详细信息

    Returns:
        格式化后的字符串 (JSON/YAML) 或 Rich Table 对象
    """
    if not task_data:
        return ""

    if format.lower() == "json":
        # 如果不需要详细信息，移除一些字段
        if not verbose:
            task_data = {k: v for k, v in task_data.items() if k in ["id", "title", "status", "assignee", "story_id", "created_at"]}
        return json.dumps(task_data, ensure_ascii=False, indent=2)
    elif format.lower() == "yaml":
        # 如果不需要详细信息，移除一些字段
        if not verbose:
            task_data = {k: v for k, v in task_data.items() if k in ["id", "title", "status", "assignee", "story_id", "created_at"]}
        return yaml.safe_dump(task_data, allow_unicode=True, sort_keys=False)
    else:  # 默认为表格输出
        return format_task_table(task_data, verbose=verbose)


def format_task_table(task_data: Dict[str, Any], verbose: bool = False) -> Table:
    """生成任务信息表格

    Args:
        task_data: 任务数据字典
        verbose: 是否显示详细信息

    Returns:
        Rich Table 对象
    """
    table = Table(title=f"任务详情: {task_data.get('title', task_data.get('id', ''))}", show_header=False, box=None, padding=(0, 1))

    # 添加列
    table.add_column("字段", style="bold cyan", width=15, no_wrap=True)
    table.add_column("值", style="white")

    # 定义要显示的字段和顺序
    fields_to_display = [
        ("ID", "id"),
        ("标题", "title"),
        ("状态", "status"),
        ("优先级", "priority"),
        ("负责人", "assignee"),
        ("标签", "labels"),
        ("截止日期", "due_date"),
        ("关联故事", "story_id"),
        ("GitHub Issue", "github_issue"),
        ("当前会话", "current_session_id"),
        ("创建时间", "created_at"),
        ("更新时间", "updated_at"),
        ("完成时间", "completed_at"),
    ]

    # 如果需要详细信息，添加描述
    if verbose:
        fields_to_display.insert(2, ("描述", "description"))  # 在标题后插入描述

    # 添加行数据
    for display_name, field_name in fields_to_display:
        value = task_data.get(field_name)

        # 只显示有值的字段，或ID/标题/状态等核心字段
        if value is not None or field_name in ["id", "title", "status"]:
            if value is None:
                value_str = "-"
            elif isinstance(value, list):
                # 将列表格式化为逗号分隔的字符串
                value_str = ", ".join(map(str, value)) if value else "-"
            elif isinstance(value, bool):
                value_str = str(value)
            elif isinstance(value, (datetime, date)):  # 假设时间是 datetime 对象
                value_str = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                value_str = str(value)

            # 特殊处理描述，允许换行
            if field_name == "description" and verbose:
                table.add_row(display_name, "")  # 先加字段名行
                # 再加描述内容，可能有多行
                console.print(Panel(Markdown(value_str if value_str != "-" else "无描述"), title="描述", border_style="dim", padding=(0, 1)))
            elif value_str != "-":  # 对于非描述字段，值不为空时才添加行
                table.add_row(display_name, value_str)
            elif field_name in ["id", "title", "status"]:  # 保证核心字段即使为空也显示
                table.add_row(display_name, "-")

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
