"""
路线图列表命令处理程序

处理列出路线图或路线图元素的命令逻辑。
"""

import json
from typing import Any, Dict, List

from rich.console import Console

console = Console()


def handle_list_command(args: Dict[str, Any], service) -> Dict[str, Any]:
    """处理路线图列表命令

    Args:
        args: 命令参数字典
        service: 路线图服务实例

    Returns:
        Dict[str, Any]: 处理结果
    """
    if args.get("all"):
        # 列出所有路线图（原all命令功能）
        return _list_all_roadmaps(service, args)
    else:
        # 列出当前路线图中的元素
        return _list_roadmap_elements(service, args)


def _list_all_roadmaps(service, args: Dict[str, Any]) -> Dict[str, Any]:
    """列出所有路线图"""
    result = service.list_roadmaps()

    if not result.get("success", False):
        return {"status": "error", "message": result.get("message", "获取路线图列表失败"), "formatted_output": ""}

    roadmaps = result.get("roadmaps", [])
    active_id = result.get("active_id")

    if not roadmaps:
        return {"status": "success", "formatted_output": "[yellow]没有找到任何路线图[/yellow]"}

    if args.get("format") == "json":
        return {"status": "success", "data": result, "formatted_output": json.dumps(result, ensure_ascii=False, indent=2)}

    # 使用文本格式输出
    output = []
    output.append("[bold]路线图列表:[/bold]")

    for idx, roadmap in enumerate(roadmaps, 1):
        # 使用name字段，如果不存在则尝试使用title字段，如果都不存在则显示"[未命名路线图]"
        roadmap_name = roadmap.get("name") or roadmap.get("title") or "[未命名路线图]"
        active_mark = " [green][活动][/green]" if roadmap.get("id") == active_id else ""
        output.append(f"{idx}. ID: {roadmap.get('id')} - {roadmap_name}{active_mark}")

        # 显示额外信息
        if args.get("detail") or args.get("verbose"):
            if roadmap.get("description"):
                output.append(f"   描述: {roadmap.get('description')}")

            # 如果有创建时间和更新时间，也显示出来
            if roadmap.get("created_at"):
                output.append(f"   创建时间: {roadmap.get('created_at')}")
            if roadmap.get("updated_at"):
                output.append(f"   更新时间: {roadmap.get('updated_at')}")

        # 分隔每个路线图
        if idx < len(roadmaps):
            output.append("")

    if not active_id:
        output.append("\n[yellow]提示: 没有设置活动路线图，请使用 'roadmap switch <roadmap_id>' 设置[/yellow]")

    return {"status": "success", "data": result, "formatted_output": "\n".join(output)}


def _list_roadmap_elements(service, args: Dict[str, Any]) -> Dict[str, Any]:
    """列出路线图中的元素（里程碑、故事、任务）"""
    # 获取当前活动路线图ID
    roadmap_id = service.active_roadmap_id
    if not roadmap_id:
        # 改为友好提示而非错误
        message = """[yellow]当前未设置活动路线图[/yellow]

可以通过以下命令操作:
[blue]1. 查看所有可用路线图:[/blue]
   roadmap list --all

[blue]2. 切换到特定路线图:[/blue]
   roadmap switch <roadmap_id>"""

        return {"status": "success", "message": "当前未设置活动路线图，请查看所有路线图并切换到活动路线图", "formatted_output": message}  # 改为success而非error

    # 根据类型获取不同元素
    element_type = args.get("type", "all")
    status_filter = args.get("status")
    assignee_filter = args.get("assignee")
    labels_filter = args.get("labels")

    elements = []

    if element_type in ["all", "milestone"]:
        milestones = service.get_milestones(roadmap_id)
        # 应用过滤
        if status_filter:
            milestones = [m for m in milestones if m.get("status") == status_filter]
        elements.extend([(m, "milestone") for m in milestones])

    if element_type in ["all", "story"]:
        stories = service.get_stories(roadmap_id)
        # 应用过滤
        if status_filter:
            stories = [s for s in stories if s.get("status") == status_filter]
        if assignee_filter:
            stories = [s for s in stories if s.get("assignee") == assignee_filter]
        if labels_filter:
            labels = [l.strip() for l in labels_filter.split(",")]
            stories = [s for s in stories if any(l in s.get("labels", []) for l in labels)]
        elements.extend([(s, "story") for s in stories])

    if element_type in ["all", "task"]:
        tasks = service.get_tasks(roadmap_id)
        # 应用过滤
        if status_filter:
            tasks = [t for t in tasks if t.get("status") == status_filter]
        if assignee_filter:
            tasks = [t for t in tasks if t.get("assignee") == assignee_filter]
        if labels_filter:
            labels = [l.strip() for l in labels_filter.split(",")]
            tasks = [t for t in tasks if any(l in t.get("tags", []) for l in labels)]
        elements.extend([(t, "task") for t in tasks])

    # 如果没有元素
    if not elements:
        return {"status": "success", "formatted_output": f"[yellow]未找到满足条件的{_get_type_name(element_type)}元素[/yellow]"}

    # 根据格式输出
    if args.get("format") == "json":
        result_data = {"roadmap_id": roadmap_id, "elements": [{"type": type_name, **element} for element, type_name in elements]}
        return {"status": "success", "data": result_data, "formatted_output": json.dumps(result_data, ensure_ascii=False, indent=2)}

    if args.get("format") == "table":
        return _format_elements_as_table(elements, args.get("detail", False))

    # 默认使用文本格式
    return _format_elements_as_text(elements, roadmap_id, args.get("detail", False))


def _format_elements_as_table(elements, detail=False):
    """将元素格式化为表格输出"""
    # 分组元素
    milestones = [(e, t) for e, t in elements if t == "milestone"]
    stories = [(e, t) for e, t in elements if t == "story"]
    tasks = [(e, t) for e, t in elements if t == "task"]

    output = []

    # 里程碑表格
    if milestones:
        output.append("\n## 里程碑")
        output.append("| ID | 名称 | 开始日期 | 结束日期 | 状态 |")
        output.append("| --- | --- | --- | --- | --- |")

        for milestone, _ in milestones:
            output.append(
                f"| {milestone.get('id', '')} | {milestone.get('name', '')} | {milestone.get('start_date', '')} | {milestone.get('end_date', '')} | {milestone.get('status', '')} |"
            )

    # 故事表格
    if stories:
        output.append("\n## 故事")
        output.append("| ID | 名称 | 状态 | 优先级 | 负责人 |")
        output.append("| --- | --- | --- | --- | --- |")

        for story, _ in stories:
            output.append(
                f"| {story.get('id', '')} | {story.get('title', '')} | {story.get('status', '')} | {story.get('priority', '')} | {story.get('assignee', '')} |"
            )

    # 任务表格
    if tasks:
        output.append("\n## 任务")
        output.append("| ID | 名称 | 里程碑 | 状态 | 优先级 |")
        output.append("| --- | --- | --- | --- | --- |")

        for task, _ in tasks:
            output.append(
                f"| {task.get('id', '')} | {task.get('name', '')} | {task.get('milestone_id', '')} | {task.get('status', '')} | {task.get('priority', '')} |"
            )

    return {"status": "success", "formatted_output": "\n".join(output)}


def _format_elements_as_text(elements, roadmap_id, detail=False):
    """将元素格式化为文本输出"""
    roadmap = None
    try:
        roadmap = next(r for r in elements if r[0].get("id") == roadmap_id)[0]
    except (StopIteration, IndexError):
        pass

    output = []
    roadmap_name = roadmap.get("name") if roadmap else "[未知路线图]"
    output.append(f"[bold]路线图 '{roadmap_name}' 元素列表:[/bold]")

    for element, type_name in elements:
        # 不同类型元素的格式
        if type_name == "milestone":
            output.append(f"[cyan]里程碑:[/cyan] {element.get('name')} (ID: {element.get('id')})")
            if detail:
                output.append(f"  状态: {element.get('status', '')}")
                output.append(f"  时间: {element.get('start_date', '')} 至 {element.get('end_date', '')}")
                if element.get("description"):
                    output.append(f"  描述: {element.get('description', '')}")

        elif type_name == "story":
            output.append(f"[blue]故事:[/blue] {element.get('title')} (ID: {element.get('id')})")
            if detail:
                output.append(f"  状态: {element.get('status', '')}")
                output.append(f"  优先级: {element.get('priority', '')}")
                output.append(f"  负责人: {element.get('assignee', '')}")
                if element.get("description"):
                    output.append(f"  描述: {element.get('description', '')}")

        elif type_name == "task":
            output.append(f"[green]任务:[/green] {element.get('name')} (ID: {element.get('id')})")
            if detail:
                output.append(f"  状态: {element.get('status', '')}")
                output.append(f"  优先级: {element.get('priority', '')}")
                output.append(f"  里程碑: {element.get('milestone_id', '')}")
                if element.get("description"):
                    output.append(f"  描述: {element.get('description', '')}")

        output.append("")  # 空行分隔

    return {"status": "success", "formatted_output": "\n".join(output)}


def _get_type_name(type_str):
    """获取元素类型的中文名称"""
    type_names = {"all": "所有", "milestone": "里程碑", "story": "故事", "task": "任务"}
    return type_names.get(type_str, type_str)
