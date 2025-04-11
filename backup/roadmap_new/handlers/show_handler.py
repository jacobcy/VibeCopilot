"""
路线图显示命令处理程序

处理查看路线图详情的命令逻辑。
"""

import json
from typing import Any, Dict

from rich.console import Console

console = Console()


def handle_show_command(args: Dict[str, Any], service) -> Dict[str, Any]:
    """处理路线图显示命令

    Args:
        args: 命令参数字典
        service: 路线图服务实例

    Returns:
        Dict[str, Any]: 处理结果
    """
    # 获取路线图ID，如果未指定则使用当前活动路线图
    roadmap_id = args.get("id")
    if not roadmap_id:
        roadmap_id = service.active_roadmap_id
        if not roadmap_id:
            # 改为友好提示而非错误
            message = """[yellow]当前未指定路线图ID，且未设置活动路线图[/yellow]

可以通过以下命令操作:
[blue]1. 查看所有可用路线图:[/blue]
   roadmap list --all

[blue]2. 使用ID参数查看指定路线图:[/blue]
   roadmap show --id=<roadmap_id>

[blue]3. 切换到活动路线图:[/blue]
   roadmap switch <roadmap_id>"""

            return {"status": "success", "message": "未指定路线图ID，且未设置活动路线图", "formatted_output": message}  # 改为success而非error

    # 如果指定了任务ID
    if args.get("task"):
        return _show_task(service, roadmap_id, args.get("task"), args.get("format", "table"))

    # 如果指定了里程碑ID
    if args.get("milestone"):
        return _show_milestone(service, roadmap_id, args.get("milestone"), args.get("format", "table"))

    # 如果指定了健康检查
    if args.get("health"):
        return _show_health(service, roadmap_id, args.get("format", "table"))

    # 否则显示整个路线图详情
    return _show_roadmap(service, roadmap_id, args.get("format", "table"))


def _show_roadmap(service, roadmap_id, format):
    """显示路线图详情"""
    roadmap = service.get_roadmap(roadmap_id)

    if not roadmap:
        return {"status": "error", "message": f"未找到路线图: {roadmap_id}", "formatted_output": ""}

    # 获取里程碑和任务数据
    milestones = service.get_milestones(roadmap_id)
    tasks = service.get_tasks(roadmap_id)

    # 将里程碑和任务添加到路线图数据中
    roadmap_data = {**roadmap, "milestones": milestones, "tasks": tasks}

    if format == "json":
        return {"status": "success", "data": {"roadmap": roadmap_data}, "formatted_output": json.dumps(roadmap_data, indent=2, ensure_ascii=False)}

    if format == "text":
        output = []
        output.append(f"路线图: {roadmap.get('title') or roadmap.get('name') or '[未命名路线图]'} ({roadmap_id})")
        output.append(f"描述: {roadmap.get('description', '')}")
        output.append(f"版本: {roadmap.get('version', '1.0')}")
        output.append(f"\n里程碑数量: {len(milestones)}")
        output.append(f"任务数量: {len(tasks)}")

        return {"status": "success", "data": {"roadmap": roadmap_data}, "formatted_output": "\n".join(output)}

    # 默认使用表格格式
    output = []

    # 元数据表格
    output.append(f"# 路线图: {roadmap.get('title') or roadmap.get('name') or '[未命名路线图]'} ({roadmap_id})")
    output.append("\n## 基本信息")
    output.append("| 属性 | 值 |")
    output.append("| --- | --- |")
    output.append(f"| ID | {roadmap_id} |")
    output.append(f"| 名称 | {roadmap.get('title') or roadmap.get('name') or '[未命名路线图]'} |")
    output.append(f"| 描述 | {roadmap.get('description', '')} |")
    output.append(f"| 版本 | {roadmap.get('version', '1.0')} |")
    output.append(f"| 创建时间 | {roadmap.get('created_at', '')} |")
    output.append(f"| 更新时间 | {roadmap.get('updated_at', '')} |")

    # 里程碑表格
    if milestones:
        output.append("\n## 里程碑")
        output.append("| ID | 名称 | 开始日期 | 结束日期 | 状态 |")
        output.append("| --- | --- | --- | --- | --- |")

        for milestone in milestones:
            output.append(
                f"| {milestone.get('id', '')} | {milestone.get('name', '')} | {milestone.get('start_date', '')} | {milestone.get('end_date', '')} | {milestone.get('status', '')} |"
            )

    # 任务表格
    if tasks:
        output.append("\n## 任务")
        output.append("| ID | 名称 | 里程碑 | 状态 | 优先级 |")
        output.append("| --- | --- | --- | --- | --- |")

        for task in tasks:
            output.append(
                f"| {task.get('id', '')} | {task.get('name', '')} | {task.get('milestone_id', '')} | {task.get('status', '')} | {task.get('priority', '')} |"
            )

    return {"status": "success", "data": {"roadmap": roadmap_data}, "formatted_output": "\n".join(output)}


def _show_milestone(service, roadmap_id, milestone_id, format):
    """显示里程碑详情"""
    milestones = service.get_milestones(roadmap_id)

    if not milestones:
        return {"status": "error", "message": f"未找到路线图: {roadmap_id} 的里程碑", "formatted_output": ""}

    milestone = next((m for m in milestones if m.get("id") == milestone_id), None)

    if not milestone:
        return {"status": "error", "message": f"未找到里程碑: {milestone_id}", "formatted_output": ""}

    # 获取与该里程碑相关的任务
    milestone_tasks = service.get_milestone_tasks(milestone_id, roadmap_id)

    # 将任务添加到里程碑数据中
    milestone_data = {**milestone, "tasks": milestone_tasks}

    if format == "json":
        return {
            "status": "success",
            "data": {"milestone": milestone_data},
            "formatted_output": json.dumps(milestone_data, indent=2, ensure_ascii=False),
        }

    if format == "text":
        output = []
        output.append(f"里程碑: {milestone.get('name')} ({milestone_id})")
        output.append(f"描述: {milestone.get('description', '')}")
        output.append(f"开始时间: {milestone.get('start_date', '')}")
        output.append(f"结束时间: {milestone.get('end_date', '')}")
        output.append(f"状态: {milestone.get('status', '')}")
        output.append(f"\n任务数量: {len(milestone_tasks)}")

        return {"status": "success", "data": {"milestone": milestone_data}, "formatted_output": "\n".join(output)}

    # 默认使用表格格式
    output = []

    # 元数据表格
    output.append(f"# 里程碑: {milestone.get('name')} ({milestone_id})")
    output.append("\n## 基本信息")
    output.append("| 属性 | 值 |")
    output.append("| --- | --- |")
    output.append(f"| ID | {milestone_id} |")
    output.append(f"| 描述 | {milestone.get('description', '')} |")
    output.append(f"| 开始时间 | {milestone.get('start_date', '')} |")
    output.append(f"| 结束时间 | {milestone.get('end_date', '')} |")
    output.append(f"| 状态 | {milestone.get('status', '')} |")

    # 任务表格
    if milestone_tasks:
        output.append("\n## 关联任务")
        output.append("| ID | 名称 | 状态 | 优先级 |")
        output.append("| --- | --- | --- | --- |")

        for task in milestone_tasks:
            output.append(f"| {task.get('id', '')} | {task.get('name', '')} | {task.get('status', '')} | {task.get('priority', '')} |")
    else:
        output.append("\n此里程碑没有关联任务")

    return {"status": "success", "data": {"milestone": milestone_data}, "formatted_output": "\n".join(output)}


def _show_task(service, roadmap_id, task_id, format):
    """显示任务详情"""
    tasks = service.get_tasks(roadmap_id)

    if not tasks:
        return {"status": "error", "message": f"未找到路线图: {roadmap_id} 的任务", "formatted_output": ""}

    task = next((t for t in tasks if t.get("id") == task_id), None)

    if not task:
        return {"status": "error", "message": f"未找到任务: {task_id}", "formatted_output": ""}

    if format == "json":
        return {"status": "success", "data": {"task": task}, "formatted_output": json.dumps(task, indent=2, ensure_ascii=False)}

    if format == "text":
        output = []
        output.append(f"任务: {task.get('name')} ({task_id})")
        output.append(f"描述: {task.get('description', '')}")
        output.append(f"里程碑: {task.get('milestone_id', '')}")
        output.append(f"状态: {task.get('status', '')}")
        output.append(f"优先级: {task.get('priority', '')}")
        output.append(f"负责人: {task.get('assignee', '')}")
        if task.get("tags"):
            output.append(f"标签: {', '.join(task.get('tags', []))}")

        return {"status": "success", "data": {"task": task}, "formatted_output": "\n".join(output)}

    # 默认使用表格格式
    output = []

    # 元数据表格
    output.append(f"# 任务: {task.get('name')} ({task_id})")
    output.append("\n## 基本信息")
    output.append("| 属性 | 值 |")
    output.append("| --- | --- |")
    output.append(f"| ID | {task_id} |")
    output.append(f"| 描述 | {task.get('description', '')} |")
    output.append(f"| 里程碑 | {task.get('milestone_id', '')} |")
    output.append(f"| 状态 | {task.get('status', '')} |")
    output.append(f"| 优先级 | {task.get('priority', '')} |")
    output.append(f"| 负责人 | {task.get('assignee', '')} |")

    if task.get("tags"):
        output.append(f"| 标签 | {', '.join(task.get('tags', []))} |")

    return {"status": "success", "data": {"task": task}, "formatted_output": "\n".join(output)}


def _show_health(service, roadmap_id, format):
    """显示路线图健康状态"""
    # 调用路线图状态检查
    health_result = service.check_roadmap_status("entire", None, roadmap_id)

    if not health_result:
        return {"status": "error", "message": f"获取路线图 {roadmap_id} 健康状态失败", "formatted_output": ""}

    if format == "json":
        return {"status": "success", "data": {"health": health_result}, "formatted_output": json.dumps(health_result, indent=2, ensure_ascii=False)}

    if format == "text":
        output = []
        output.append(f"路线图健康状态: {roadmap_id}")
        output.append(f"整体健康度: {health_result.get('status', {}).get('health_score', '未知')}%")
        output.append(f"状态: {health_result.get('status', {}).get('status', '未知')}")

        if "issues" in health_result and health_result["issues"]:
            output.append("\n问题:")
            for issue in health_result["issues"]:
                output.append(f"- {issue}")

        if "recommendations" in health_result and health_result["recommendations"]:
            output.append("\n建议:")
            for rec in health_result["recommendations"]:
                output.append(f"- {rec}")

        return {"status": "success", "data": {"health": health_result}, "formatted_output": "\n".join(output)}

    # 默认使用表格格式
    output = []

    # 元数据表格
    output.append(f"# 路线图健康状态: {roadmap_id}")
    output.append("\n## 基本信息")
    output.append("| 属性 | 值 |")
    output.append("| --- | --- |")
    output.append(f"| 整体健康度 | {health_result.get('status', {}).get('health_score', '未知')}% |")
    output.append(f"| 状态 | {health_result.get('status', {}).get('status', '未知')} |")

    # 问题表格
    if "issues" in health_result and health_result["issues"]:
        output.append("\n## 问题")
        for issue in health_result["issues"]:
            output.append(f"- {issue}")

    # 建议表格
    if "recommendations" in health_result and health_result["recommendations"]:
        output.append("\n## 建议")
        for rec in health_result["recommendations"]:
            output.append(f"- {rec}")

    return {"status": "success", "data": {"health": health_result}, "formatted_output": "\n".join(output)}
