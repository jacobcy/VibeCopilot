"""
路线图显示处理器

处理路线图、里程碑和任务的详情显示。
"""

import json
import logging
from typing import Dict, Optional

from rich.console import Console
from tabulate import tabulate

from src.roadmap import RoadmapService

console = Console()
logger = logging.getLogger(__name__)


def handle_show_roadmap(
    service: RoadmapService,
    roadmap_id: Optional[str] = None,
    milestone_id: Optional[str] = None,
    task_id: Optional[str] = None,
    health: bool = False,
    format: str = "table",
) -> Dict:
    """处理路线图显示"""
    try:
        # 获取路线图ID
        roadmap_id = roadmap_id or service.active_roadmap_id
        if not roadmap_id:
            return {"success": False, "message": "未指定路线图ID，且未设置活动路线图。请指定ID或使用 'roadmap switch <roadmap_id>' 设置活动路线图。"}

        # 根据参数选择显示内容
        if task_id:
            return handle_show_task(service, roadmap_id, task_id, format)
        elif milestone_id:
            return handle_show_milestone(service, roadmap_id, milestone_id, format)
        elif health:
            return handle_show_health(service, roadmap_id, format)
        else:
            return handle_show_roadmap_details(service, roadmap_id, format)

    except Exception as e:
        return {"success": False, "message": f"显示路线图时出错: {str(e)}"}


def handle_show_roadmap_details(service: RoadmapService, roadmap_id: str, format: str) -> Dict:
    """显示路线图详情"""
    try:
        roadmap = service.get_roadmap(roadmap_id)
        if not roadmap:
            return {"success": False, "message": f"未找到路线图: {roadmap_id}"}

        # 获取里程碑和任务数据
        milestones = service.get_milestones(roadmap_id)
        tasks = service.get_tasks(roadmap_id)
        logger.debug(f"[handle_show_roadmap_details] Received {len(tasks)} tasks from service.get_tasks for roadmap {roadmap_id}.")

        # 将里程碑和任务添加到路线图数据中
        roadmap_data = {**roadmap, "milestones": milestones, "tasks": tasks}

        if format == "json":
            formatted_output = json.dumps(roadmap_data, indent=2, ensure_ascii=False)
        elif format == "text":
            output = []
            output.append(f"路线图: {roadmap.get('title') or roadmap.get('name') or '[未命名路线图]'} ({roadmap_id})")
            output.append(f"描述: {roadmap.get('description', '')}")
            output.append(f"版本: {roadmap.get('version', '1.0')}")
            output.append(f"\n里程碑数量: {len(milestones)}")
            output.append(f"任务数量: {len(tasks)}")
            formatted_output = "\n".join(output)
        else:
            # 默认使用表格格式
            output = []
            output.append(f"# 路线图: {roadmap.get('title') or roadmap.get('name') or '[未命名路线图]'} ({roadmap_id})")

            # 基本信息表格
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
                        f"| {milestone.get('id', '')} | {milestone.get('name', '')} | "
                        f"{milestone.get('start_date', '')} | {milestone.get('end_date', '')} | "
                        f"{milestone.get('status', '')} |"
                    )

            # 任务表格
            if tasks:
                logger.debug(f"[handle_show_roadmap_details] Generating task table for {len(tasks)} tasks.")
                output.append("\n## 任务")
                output.append("| ID | 任务标题 | Story 标题 | 里程碑 | 状态 | 优先级 |")
                output.append("| --- | --- | --- | --- | --- | --- |")
                for task in tasks:
                    output.append(
                        f"| {task.get('id', '')} | {task.get('title', '')} | "
                        f"{task.get('story_title', 'N/A')} | "
                        f"{task.get('milestone_id', '')} | {task.get('status', '')} | "
                        f"{task.get('priority', '')} |"
                    )

            formatted_output = "\n".join(output)

        return {"success": True, "data": {"roadmap": roadmap_data, "formatted_output": formatted_output}}

    except Exception as e:
        return {"success": False, "message": f"显示路线图详情时出错: {str(e)}"}


def handle_show_milestone(service: RoadmapService, roadmap_id: str, milestone_id: str, format: str) -> Dict:
    """显示里程碑详情"""
    try:
        milestones = service.get_milestones(roadmap_id)
        if not milestones:
            return {"success": False, "message": f"未找到路线图: {roadmap_id} 的里程碑"}

        milestone = next((m for m in milestones if m.get("id") == milestone_id), None)
        if not milestone:
            return {"success": False, "message": f"未找到里程碑: {milestone_id}"}

        # 获取与该里程碑相关的任务
        milestone_tasks = service.get_milestone_tasks(milestone_id, roadmap_id)
        milestone_data = {**milestone, "tasks": milestone_tasks}

        if format == "json":
            formatted_output = json.dumps(milestone_data, indent=2, ensure_ascii=False)
        elif format == "text":
            output = []
            output.append(f"里程碑: {milestone.get('name')} ({milestone_id})")
            output.append(f"描述: {milestone.get('description', '')}")
            output.append(f"开始时间: {milestone.get('start_date', '')}")
            output.append(f"结束时间: {milestone.get('end_date', '')}")
            output.append(f"状态: {milestone.get('status', '')}")
            output.append(f"\n任务数量: {len(milestone_tasks)}")
            formatted_output = "\n".join(output)
        else:
            # 默认使用表格格式
            output = []
            output.append(f"# 里程碑: {milestone.get('name')} ({milestone_id})")

            # 基本信息表格
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
                    output.append(f"| {task.get('id', '')} | {task.get('name', '')} | " f"{task.get('status', '')} | {task.get('priority', '')} |")
            else:
                output.append("\n此里程碑没有关联任务")

            formatted_output = "\n".join(output)

        return {"success": True, "data": {"milestone": milestone_data, "formatted_output": formatted_output}}

    except Exception as e:
        return {"success": False, "message": f"显示里程碑详情时出错: {str(e)}"}


def handle_show_task(service: RoadmapService, roadmap_id: str, task_id: str, format: str) -> Dict:
    """显示任务详情"""
    try:
        tasks = service.get_tasks(roadmap_id)
        if not tasks:
            return {"success": False, "message": f"未找到路线图: {roadmap_id} 的任务"}

        task = next((t for t in tasks if t.get("id") == task_id), None)
        if not task:
            return {"success": False, "message": f"未找到任务: {task_id}"}

        if format == "json":
            formatted_output = json.dumps(task, indent=2, ensure_ascii=False)
        elif format == "text":
            output = []
            output.append(f"任务: {task.get('name')} ({task_id})")
            output.append(f"描述: {task.get('description', '')}")
            output.append(f"里程碑: {task.get('milestone_id', '')}")
            output.append(f"状态: {task.get('status', '')}")
            output.append(f"优先级: {task.get('priority', '')}")
            output.append(f"负责人: {task.get('assignee', '')}")
            if task.get("tags"):
                output.append(f"标签: {', '.join(task.get('tags', []))}")
            formatted_output = "\n".join(output)
        else:
            # 默认使用表格格式
            output = []
            output.append(f"# 任务: {task.get('name')} ({task_id})")

            # 基本信息表格
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

            formatted_output = "\n".join(output)

        return {"success": True, "data": {"task": task, "formatted_output": formatted_output}}

    except Exception as e:
        return {"success": False, "message": f"显示任务详情时出错: {str(e)}"}


def handle_show_health(service: RoadmapService, roadmap_id: str, format: str) -> Dict:
    """显示路线图健康状态"""
    try:
        health_result = service.check_roadmap_status("entire", None, roadmap_id)
        if not health_result:
            return {"success": False, "message": f"获取路线图 {roadmap_id} 健康状态失败"}

        if format == "json":
            formatted_output = json.dumps(health_result, indent=2, ensure_ascii=False)
        elif format == "text":
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

            formatted_output = "\n".join(output)
        else:
            # 默认使用表格格式
            output = []
            output.append(f"# 路线图健康状态: {roadmap_id}")

            # 基本信息表格
            output.append("\n## 基本信息")
            output.append("| 属性 | 值 |")
            output.append("| --- | --- |")
            output.append(f"| 整体健康度 | {health_result.get('status', {}).get('health_score', '未知')}% |")
            output.append(f"| 状态 | {health_result.get('status', {}).get('status', '未知')} |")

            # 问题列表
            if "issues" in health_result and health_result["issues"]:
                output.append("\n## 问题")
                for issue in health_result["issues"]:
                    output.append(f"- {issue}")

            # 建议列表
            if "recommendations" in health_result and health_result["recommendations"]:
                output.append("\n## 建议")
                for rec in health_result["recommendations"]:
                    output.append(f"- {rec}")

            formatted_output = "\n".join(output)

        return {"success": True, "data": {"health": health_result, "formatted_output": formatted_output}}

    except Exception as e:
        return {"success": False, "message": f"显示健康状态时出错: {str(e)}"}
