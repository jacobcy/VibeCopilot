"""
路线图列表处理器

处理路线图元素的列表查询，支持多种筛选和格式化选项。
"""

import json
from typing import Dict, List, Optional

from rich.console import Console
from tabulate import tabulate

from src.roadmap import RoadmapService

console = Console()


def handle_list_elements(
    service: RoadmapService,
    type: str = "all",
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[str] = None,
    detail: bool = False,
    format: str = "text",
    verbose: bool = False,
) -> Dict:
    """处理元素列表查询"""
    try:
        # 验证当前有活动路线图
        if not service.active_roadmap_id:
            return {"success": False, "message": "未设置活动路线图，请使用 'roadmap switch <roadmap_id>' 设置活动路线图，或使用 'roadmap list --all' 查看所有可用路线图"}

        # 准备查询参数
        query_params = {
            "type": type,
            "status": status,
            "assignee": assignee,
            "labels": labels.split(",") if labels else None,
            "sort_by": "id",
            "sort_desc": False,
            "page": 1,
            "page_size": 100,
        }

        # 执行查询
        result = service.list_elements(**query_params)

        if not result.get("success", False):
            return {"success": False, "message": result.get("message", "查询元素失败")}

        # 格式化输出
        formatted = format_output(
            data=result.get("data", []),
            format=format,
            type=type,
            detail=detail,
            verbose=verbose,
        )

        return {"success": True, "data": result.get("data", []), "formatted_output": formatted, "total": len(result.get("data", []))}

    except Exception as e:
        return {"success": False, "message": f"执行出错: {str(e)}"}


def handle_list_roadmaps(service: RoadmapService, detail: bool = False, format: str = "text", verbose: bool = False) -> Dict:
    """处理路线图列表查询"""
    try:
        result = service.list_roadmaps()

        if not result.get("success", False):
            return {"success": False, "message": result.get("message", "获取路线图列表失败")}

        roadmaps = result.get("roadmaps", [])
        active_id = result.get("active_id")

        if not roadmaps:
            return {"success": True, "message": "没有找到任何路线图", "roadmaps": [], "active_id": None}

        # 格式化输出
        formatted = format_roadmaps_output(roadmaps=roadmaps, active_id=active_id, format=format, detail=detail, verbose=verbose)

        return {"success": True, "roadmaps": roadmaps, "active_id": active_id, "formatted_output": formatted}

    except Exception as e:
        return {"success": False, "message": f"执行出错: {str(e)}"}


def format_output(data: list, format: str, type: str, detail: bool, verbose: bool) -> str:
    """格式化元素列表输出"""
    if not data:
        type_name = {"all": "所有类型", "milestone": "里程碑", "story": "故事", "task": "任务"}.get(type, "元素")
        return f"没有找到匹配的{type_name}，当前路线图可能未包含此类元素或符合筛选条件的元素"

    if format == "json":
        return json.dumps(data, ensure_ascii=False, indent=2)

    if format == "table":
        headers = ["ID", "名称", "类型", "状态"]
        if detail or verbose:
            headers.extend(["优先级", "进度", "指派人"])

        rows = []
        for item in data:
            row = [item.get("id", ""), item.get("name", ""), item.get("type", ""), item.get("status", "")]
            if detail or verbose:
                row.extend([item.get("priority", ""), f"{item.get('progress', 0)}%", item.get("assignee", "")])
            rows.append(row)

        return tabulate(rows, headers=headers, tablefmt="grid")

    # 默认文本格式
    output = []
    type_name = {"all": "所有元素", "milestone": "里程碑", "story": "故事", "task": "任务"}.get(type, "元素")
    output.append(f"路线图{type_name}列表:")

    for item in data:
        output.append(f"- {item.get('name')} (ID: {item.get('id')}, 状态: {item.get('status')})")

        if detail or verbose:
            if "description" in item and item["description"]:
                output.append(f"  描述: {item['description']}")
            if "priority" in item:
                output.append(f"  优先级: {item['priority']}")
            if "progress" in item:
                output.append(f"  进度: {item['progress']}%")
            if "assignee" in item and item["assignee"]:
                output.append(f"  指派人: {item['assignee']}")
            if "labels" in item and item["labels"]:
                labels_str = ", ".join(item["labels"])
                output.append(f"  标签: {labels_str}")
            output.append("")

    return "\n".join(output)


def format_roadmaps_output(roadmaps: List[Dict], active_id: Optional[str], format: str, detail: bool, verbose: bool) -> str:
    """格式化路线图列表输出"""
    if format == "json":
        return json.dumps({"roadmaps": roadmaps, "active_id": active_id}, ensure_ascii=False, indent=2)

    output = []
    output.append("[bold]路线图列表:[/bold]")

    for idx, roadmap in enumerate(roadmaps, 1):
        roadmap_name = roadmap.get("name") or roadmap.get("title") or "[未命名路线图]"
        active_mark = " [green][活动][/green]" if roadmap.get("id") == active_id else ""
        output.append(f"{idx}. ID: {roadmap.get('id')} - {roadmap_name}{active_mark}")

        if detail or verbose:
            if roadmap.get("description"):
                output.append(f"   描述: {roadmap.get('description')}")
            if roadmap.get("created_at"):
                output.append(f"   创建时间: {roadmap.get('created_at')}")
            if roadmap.get("updated_at"):
                output.append(f"   更新时间: {roadmap.get('updated_at')}")

        if idx < len(roadmaps):
            output.append("")

    if not active_id:
        output.append("\n[yellow]提示: 没有设置活动路线图，请使用 'roadmap switch <roadmap_id>' 设置[/yellow]")

    return "\n".join(output)
