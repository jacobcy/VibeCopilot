"""
路线图格式化模块

处理路线图数据的格式化和输出。
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def format_roadmap_data(roadmap: Dict[str, Any], format_type: str = "json") -> Dict[str, Any]:
    """
    格式化路线图数据

    Args:
        roadmap: 路线图数据
        format_type: 输出格式，支持json, markdown等

    Returns:
        Dict[str, Any]: 格式化后的路线图数据
    """
    # 保留原始数据的拷贝
    result = roadmap.copy()

    # 处理日期格式
    result = _format_dates(result)

    # 计算派生数据
    result = _calculate_derived_data(result)

    # 根据输出格式进行特定处理
    if format_type == "markdown":
        result["markdown"] = _generate_markdown(result)
    elif format_type == "html":
        result["html"] = _generate_html(result)

    return result


def _format_dates(roadmap: Dict[str, Any]) -> Dict[str, Any]:
    """格式化路线图中的日期"""
    result = roadmap.copy()

    # 格式化生成日期
    if "generated_at" in result and isinstance(result["generated_at"], datetime):
        result["generated_at"] = result["generated_at"].isoformat()

    # 格式化里程碑日期
    if "milestones" in result:
        for milestone in result["milestones"]:
            if "start_date" in milestone and isinstance(milestone["start_date"], datetime):
                milestone["start_date"] = milestone["start_date"].isoformat()
            if "end_date" in milestone and isinstance(milestone["end_date"], datetime):
                milestone["end_date"] = milestone["end_date"].isoformat()

    # 格式化任务日期
    if "tasks" in result:
        for task in result["tasks"]:
            if "due_date" in task and isinstance(task["due_date"], datetime):
                task["due_date"] = task["due_date"].isoformat()

    return result


def _calculate_derived_data(roadmap: Dict[str, Any]) -> Dict[str, Any]:
    """计算路线图的派生数据，如总进度、总任务数等"""
    result = roadmap.copy()

    # 统计任务信息
    if "tasks" in result:
        tasks = result["tasks"]
        total_tasks = len(tasks)

        # 计算任务状态分布
        status_counts = {}
        for task in tasks:
            status = task.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # 计算总体进度
        completed_tasks = status_counts.get("completed", 0)
        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # 将派生数据添加到结果中
        result["task_stats"] = {
            "total": total_tasks,
            "status_counts": status_counts,
            "overall_progress": round(overall_progress, 2),
        }

    return result


def _generate_markdown(roadmap: Dict[str, Any]) -> str:
    """生成路线图的Markdown表示"""
    md = []

    # 标题
    md.append(f"# {roadmap.get('title', 'Project Roadmap')}")
    md.append("")

    # 描述
    if roadmap.get("description"):
        md.append(roadmap["description"])
        md.append("")

    # 生成日期
    if roadmap.get("generated_at"):
        md.append(f"*生成于: {roadmap['generated_at']}*")
        md.append("")

    # 总体进度
    if "task_stats" in roadmap:
        progress = roadmap["task_stats"]["overall_progress"]
        md.append(f"## 总体进度: {progress}%")
        md.append("")

    # 里程碑
    if roadmap.get("milestones"):
        md.append("## 里程碑")
        md.append("")

        for milestone in roadmap["milestones"]:
            md.append(f"### {milestone.get('name', 'Unnamed Milestone')}")

            if milestone.get("description"):
                md.append("")
                md.append(milestone["description"])

            if "start_date" in milestone and "end_date" in milestone:
                md.append("")
                md.append(f"*{milestone['start_date']} - {milestone['end_date']}*")

            if "progress" in milestone:
                md.append("")
                md.append(f"进度: {milestone['progress']}%")

            md.append("")

    # 任务
    if roadmap.get("tasks"):
        md.append("## 任务")
        md.append("")

        for task in roadmap["tasks"]:
            status = task.get("status", "")
            status_marker = "✅" if status == "completed" else "⬜"

            md.append(f"- {status_marker} **{task.get('title', 'Unnamed Task')}** ({status})")

            if task.get("description"):
                md.append(f"  {task['description']}")

            if task.get("assignees"):
                assignees = ", ".join(task["assignees"])
                md.append(f"  *分配给: {assignees}*")

            md.append("")

    return "\n".join(md)


def _generate_html(roadmap: Dict[str, Any]) -> str:
    """生成路线图的HTML表示"""
    # 简化实现，实际项目中可以使用模板引擎
    html = ["<html><head><title>Project Roadmap</title></head><body>"]

    html.append(f"<h1>{roadmap.get('title', 'Project Roadmap')}</h1>")

    if roadmap.get("description"):
        html.append(f"<p>{roadmap['description']}</p>")

    # 这里添加更多HTML生成逻辑...

    html.append("</body></html>")

    return "\n".join(html)
