"""
路线图故事命令处理程序

处理查看路线图故事的命令逻辑。
"""

import json
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

console = Console()


def handle_story_command(args: Dict[str, Any], service) -> Dict[str, Any]:
    """处理路线图故事命令

    Args:
        args: 命令参数字典
        service: 路线图服务实例

    Returns:
        Dict[str, Any]: 处理结果
    """
    story_id = args.get("story_id")

    # 如果提供了具体的故事ID，显示该故事的详情
    if story_id:
        return _show_story_detail(service, args)

    # 否则，列出符合筛选条件的故事
    return _list_stories(args, service)


def _show_story_detail(service: RoadmapService, args: Dict) -> Dict:
    """
    显示故事详情

    参数:
        service: 路线图服务实例
        args: 命令参数

    返回:
        操作结果字典
    """
    # 获取必要参数
    roadmap_id = args.get("roadmap_id")
    story_id = args.get("story_id")
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

[blue]3. 指定路线图ID执行故事命令:[/blue]
   story get --roadmap-id=<roadmap_id> --story-id=<story_id>"""

            return {"status": "success", "message": "未指定路线图ID，且未设置活动路线图", "formatted_output": message}  # 改为success而非error

    if not story_id:
        message = """[yellow]未指定故事ID[/yellow]

可以通过以下命令操作:
[blue]1. 查看当前路线图的所有故事:[/blue]
   story list

[blue]2. 指定故事ID查看详情:[/blue]
   story get --story-id=<story_id>"""

        return {"status": "success", "message": "缺少故事ID", "formatted_output": message}

    # 获取故事详情
    story_result = service.get_story(roadmap_id, story_id)

    # 检查是否存在此故事
    if not story_result or "error" in story_result:
        error_msg = story_result.get("error", "未知错误") if story_result else "获取故事详情失败"
        return {"status": "error", "message": error_msg, "formatted_output": f"错误: {error_msg}"}

    # 获取相关任务
    tasks_result = service.list_tasks(roadmap_id, {"story_id": story_id})
    tasks = tasks_result.get("tasks", []) if tasks_result and "tasks" in tasks_result else []

    # 将任务添加到故事数据中
    story_data = {**story_result, "tasks": tasks}

    # 根据格式类型返回
    if format_type == "json":
        return {"status": "success", "data": story_data, "formatted_output": json.dumps(story_data, ensure_ascii=False, indent=2)}

    if format_type == "yaml":
        import yaml

        return {"status": "success", "data": story_data, "formatted_output": yaml.dump(story_data, allow_unicode=True, sort_keys=False)}

    # 默认使用表格格式
    output = []

    output.append(f"# 故事详情: {story_data.get('title', '无标题')}")
    output.append("")
    output.append(f"ID: {story_data.get('id', '无ID')}")
    output.append(f"标题: {story_data.get('title', '无标题')}")
    output.append(f"状态: {story_data.get('status', '未设置')}")
    output.append(f"优先级: {story_data.get('priority', '未设置')}")
    output.append(f"负责人: {story_data.get('assignee', '未分配')}")
    output.append(f"标签: {', '.join(story_data.get('labels', []))}")
    output.append(f"里程碑: {story_data.get('milestone_id', '未关联')}")
    output.append("")
    output.append("## 描述")
    output.append("")
    output.append(story_data.get("description", "无描述"))
    output.append("")

    # 添加任务列表
    if tasks:
        output.append("## 相关任务")
        output.append("")
        output.append("| ID | 标题 | 状态 | 优先级 | 负责人 |")
        output.append("| --- | --- | --- | --- | --- |")

        for task in tasks:
            output.append(
                f"| {task.get('id', '')} | {task.get('title', '')} | {task.get('status', '')} | {task.get('priority', '')} | {task.get('assignee', '')} |"
            )
    else:
        output.append("## 相关任务")
        output.append("")
        output.append("暂无相关任务")

    return {"status": "success", "data": story_data, "formatted_output": "\n".join(output)}


def _list_stories(args: Dict[str, Any], service) -> Dict[str, Any]:
    """列出符合筛选条件的故事"""
    # 获取当前活动路线图ID
    roadmap_id = service.active_roadmap_id
    if not roadmap_id:
        # 改为友好提示而非错误
        message = """[yellow]当前未设置活动路线图[/yellow]

可以通过以下命令操作:
[blue]1. 查看所有可用路线图:[/blue]
   roadmap list --all

[blue]2. 切换到活动路线图:[/blue]
   roadmap switch <roadmap_id>"""

        return {"status": "success", "message": "未设置活动路线图", "formatted_output": message}

    # 获取筛选参数
    milestone_id = args.get("milestone")
    status = args.get("status")
    assignee = args.get("assignee")
    labels = args.get("labels")
    sort_field = args.get("sort", "id")
    desc_order = args.get("desc", False)
    format_type = args.get("format", "table")

    # 解析标签
    label_list = None
    if labels:
        label_list = [label.strip() for label in labels.split(",")]

    try:
        # 获取故事列表
        stories = service.get_stories(roadmap_id)

        if not stories:
            return {"status": "success", "message": "没有找到故事", "formatted_output": "没有找到故事"}

        # 应用筛选条件
        filtered_stories = stories

        if milestone_id:
            filtered_stories = [s for s in filtered_stories if s.get("milestone_id") == milestone_id]

        if status:
            filtered_stories = [s for s in filtered_stories if s.get("status") == status]

        if assignee:
            filtered_stories = [s for s in filtered_stories if s.get("assignee") == assignee]

        if label_list:
            filtered_stories = [s for s in filtered_stories if set(label_list).issubset(set(s.get("labels", [])))]

        # 如果筛选后没有结果
        if not filtered_stories:
            return {"status": "success", "message": "没有符合条件的故事", "formatted_output": "没有符合条件的故事"}

        # 排序
        if sort_field in ["id", "title", "status", "priority", "assignee"]:
            # 默认以ID升序排序
            filtered_stories.sort(key=lambda x: x.get(sort_field, ""), reverse=desc_order)

        # 根据格式输出结果
        if format_type == "json":
            return {
                "status": "success",
                "data": {"stories": filtered_stories},
                "formatted_output": json.dumps({"stories": filtered_stories}, ensure_ascii=False, indent=2),
            }

        if format_type == "yaml":
            import yaml

            return {
                "status": "success",
                "data": {"stories": filtered_stories},
                "formatted_output": yaml.dump({"stories": filtered_stories}, allow_unicode=True, sort_keys=False),
            }

        # 默认使用表格格式
        output = []

        output.append("# 路线图故事列表")
        output.append("\n| ID | 标题 | 状态 | 优先级 | 负责人 |")
        output.append("| --- | --- | --- | --- | --- |")

        for story in filtered_stories:
            output.append(
                f"| {story.get('id', '')} | {story.get('title', '')} | {story.get('status', '')} | {story.get('priority', '')} | {story.get('assignee', '')} |"
            )

        return {"status": "success", "data": {"stories": filtered_stories}, "formatted_output": "\n".join(output)}

    except Exception as e:
        return {"status": "error", "message": f"获取故事列表时发生错误: {str(e)}"}
