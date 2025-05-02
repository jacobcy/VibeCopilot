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


def handle_list_roadmaps(service: RoadmapService, verbose: bool = False) -> Dict:
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
        formatted = format_roadmaps_output(roadmaps=roadmaps, active_id=active_id, verbose=verbose)

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


def format_roadmaps_output(roadmaps: List[Dict], active_id: Optional[str], verbose: bool = False) -> str:
    """格式化路线图列表输出"""
    # 创建一个字符串IO控制台来捕获输出
    from io import StringIO

    from rich.console import Console
    from rich.text import Text

    string_io = StringIO()
    rich_console = Console(file=string_io, highlight=False)

    if not roadmaps:
        rich_console.print("[yellow]没有找到任何路线图[/yellow]")
        return string_io.getvalue()

    for roadmap in roadmaps:
        roadmap_id = roadmap.get("id", "")
        title = roadmap.get("title") or roadmap.get("name") or "[未命名路线图]"
        is_active = roadmap_id == active_id

        # 创建路线图面板内容
        content = []

        # 添加基本信息
        if is_active:
            content.append(Text("- id: ", style="bold cyan") + Text(roadmap_id) + Text(" [活动]", style="green bold"))
        else:
            content.append(Text("- id: ", style="bold cyan") + Text(roadmap_id))

        content.append(Text("  title: ", style="bold cyan") + Text(title))

        # 添加描述
        description = roadmap.get("description", "")
        if description:
            # 如果描述太长，截断它
            if len(description) > 100 and not verbose:
                description = description[:97] + "..."
            content.append(Text("  description: ", style="bold cyan") + Text(description))

        # 添加版本
        version = roadmap.get("version", "")
        if version:
            content.append(Text("  version: ", style="bold cyan") + Text(str(version)))

        # 添加状态
        status = roadmap.get("status", "")
        if status:
            content.append(Text("  status: ", style="bold cyan") + Text(status))

        # 如果是详细模式，添加更多信息
        if verbose:
            # 添加创建和更新时间
            created_at = roadmap.get("created_at", "")
            if created_at:
                content.append(Text("  created_at: ", style="bold cyan") + Text(str(created_at)))

            updated_at = roadmap.get("updated_at", "")
            if updated_at:
                content.append(Text("  updated_at: ", style="bold cyan") + Text(str(updated_at)))

            # 添加里程碑和史诗数量
            milestones_count = roadmap.get("milestones_count", 0)
            content.append(Text("  milestones_count: ", style="bold cyan") + Text(str(milestones_count)))

            epics_count = roadmap.get("epics_count", 0)
            content.append(Text("  epics_count: ", style="bold cyan") + Text(str(epics_count)))

        # 打印路线图信息
        for line in content:
            rich_console.print(line)

        # 添加空行分隔不同的路线图
        rich_console.print("")

    # 如果没有活动路线图，添加提示
    if not active_id:
        rich_console.print("[yellow]提示: 没有设置活动路线图，请使用 'roadmap switch <roadmap_id>' 设置[/yellow]")

    # 如果是详细模式，显示总数
    if verbose and roadmaps:
        rich_console.print(f"\n共 {len(roadmaps)} 个路线图")

    return string_io.getvalue()
