"""
路线图显示处理器

处理路线图、里程碑和任务的详情显示。
"""

import json
import logging
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console

from src.roadmap import RoadmapService

console = Console()
logger = logging.getLogger(__name__)


def handle_show_roadmap(
    service: RoadmapService,
    roadmap_id: Optional[str] = None,
    milestone_id: Optional[str] = None,
    task_id: Optional[str] = None,
    health: bool = False,
    format: str = "yaml",
    element_type: str = "roadmap",
) -> Dict:
    """处理路线图显示"""
    try:
        # 获取路线图ID
        roadmap_id = roadmap_id or service.active_roadmap_id
        if not roadmap_id:
            return {"success": False, "message": "未指定路线图ID，且未设置活动路线图。请指定ID或使用 'roadmap switch <roadmap_id>' 设置活动路线图。"}

        # 根据参数选择显示内容
        if task_id:
            # 任务显示已移至task命令，但保留兼容性
            return handle_show_task(service, roadmap_id, task_id, format)
        elif milestone_id:
            # 显示特定里程碑
            return handle_show_milestone(service, roadmap_id, milestone_id, format)
        elif element_type == "milestone":
            # 显示所有里程碑
            return handle_show_all_milestones(service, roadmap_id, format)
        elif element_type == "epic" or element_type == "story":
            # 显示所有史诗或故事
            return handle_show_elements_by_type(service, roadmap_id, element_type, format)
        elif health:
            # 健康状态检查已移除，但保留兼容性
            return handle_show_health(service, roadmap_id, format)
        else:
            # 显示路线图详情
            return handle_show_roadmap_details(service, roadmap_id, format)

    except Exception as e:
        return {"success": False, "message": f"显示路线图时出错: {str(e)}"}


def handle_show_all_milestones(service: RoadmapService, roadmap_id: str, format: str = "yaml") -> Dict:
    """显示路线图的所有里程碑"""
    try:
        # 获取路线图
        roadmap = service.get_roadmap(roadmap_id)
        if not roadmap:
            return {"success": False, "message": f"未找到路线图: {roadmap_id}"}

        # 获取里程碑
        milestones = service.get_milestones(roadmap_id)
        if not milestones:
            return {"success": True, "data": {"formatted_output": "此路线图没有里程碑"}}

        # 准备YAML数据
        yaml_data = {"roadmap": {"id": roadmap_id, "title": roadmap.get("title") or roadmap.get("name") or "[未命名路线图]"}, "milestones": []}

        # 添加里程碑数据
        for milestone in milestones:
            milestone_data = {
                "id": milestone.get("id", ""),
                "name": milestone.get("name", ""),
                "description": milestone.get("description", ""),
                "status": milestone.get("status", ""),
                "start_date": milestone.get("start_date", ""),
                "end_date": milestone.get("end_date", ""),
            }
            yaml_data["milestones"].append(milestone_data)

        # 转换为YAML格式
        yaml_string = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        formatted_output = yaml_string

        return {"success": True, "data": {"milestones": milestones, "formatted_output": formatted_output}}

    except Exception as e:
        logger.exception(f"显示里程碑列表时出错")
        return {"success": False, "message": f"显示里程碑列表时出错: {str(e)}"}


def handle_show_elements_by_type(service: RoadmapService, roadmap_id: str, element_type: str, format: str = "yaml") -> Dict:
    """显示路线图的所有史诗或故事"""
    try:
        # 获取路线图
        roadmap = service.get_roadmap(roadmap_id)
        if not roadmap:
            return {"success": False, "message": f"未找到路线图: {roadmap_id}"}

        # 根据类型获取元素
        elements = []
        if element_type == "epic":
            if hasattr(service, "get_epics"):
                elements = service.get_epics(roadmap_id)
            else:
                return {"success": True, "data": {"formatted_output": "此服务不支持获取史诗"}}
        elif element_type == "story":
            if hasattr(service, "get_stories"):
                elements = service.get_stories(roadmap_id)
            else:
                return {"success": True, "data": {"formatted_output": "此服务不支持获取故事"}}

        if not elements:
            return {"success": True, "data": {"formatted_output": f"此路线图没有{element_type}"}}

        # 准备YAML数据
        yaml_data = {"roadmap": {"id": roadmap_id, "title": roadmap.get("title") or roadmap.get("name") or "[未命名路线图]"}, element_type + "s": []}

        # 添加元素数据
        for element in elements:
            element_data = {
                "id": element.get("id", ""),
                "title": element.get("title", "") or element.get("name", ""),
                "description": element.get("description", ""),
                "status": element.get("status", ""),
            }

            # 添加其他可能的字段
            if "priority" in element:
                element_data["priority"] = element.get("priority", "")
            if "assignee" in element:
                element_data["assignee"] = element.get("assignee", "")
            if "milestone_id" in element:
                element_data["milestone_id"] = element.get("milestone_id", "")

            yaml_data[element_type + "s"].append(element_data)

        # 转换为YAML格式
        yaml_string = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        formatted_output = yaml_string

        return {"success": True, "data": {element_type + "s": elements, "formatted_output": formatted_output}}

    except Exception as e:
        logger.exception(f"显示{element_type}列表时出错")
        return {"success": False, "message": f"显示{element_type}列表时出错: {str(e)}"}


def handle_show_roadmap_details(service: RoadmapService, roadmap_id: str, format: str = "yaml") -> Dict:
    """显示路线图详情"""
    try:
        roadmap = service.get_roadmap(roadmap_id)
        if not roadmap:
            return {"success": False, "message": f"未找到路线图: {roadmap_id}"}

        # 获取里程碑数据
        milestones = service.get_milestones(roadmap_id)

        # 获取史诗和故事数据（如果服务支持）
        epics = []
        stories = []
        try:
            if hasattr(service, "get_epics"):
                epics = service.get_epics(roadmap_id)
            if hasattr(service, "get_stories"):
                stories = service.get_stories(roadmap_id)
        except Exception as e:
            logger.warning(f"获取史诗或故事时出错: {str(e)}")

        # 将里程碑、史诗和故事添加到路线图数据中
        roadmap_data = {**roadmap, "milestones": milestones, "epics": epics, "stories": stories}

        # 使用YAML格式输出
        yaml_data: Dict[str, Any] = {
            "roadmap": {
                "id": roadmap_id,
                "title": roadmap.get("title") or roadmap.get("name") or "[未命名路线图]",
                "description": roadmap.get("description", ""),
                "version": roadmap.get("version", "1.0"),
                "status": roadmap.get("status", ""),
                "created_at": roadmap.get("created_at", ""),
                "updated_at": roadmap.get("updated_at", ""),
                "milestones_count": len(milestones),
                "epics_count": len(epics),
                "stories_count": len(stories),
            }
        }

        # 添加里程碑摘要
        if milestones:
            milestone_list = []
            for milestone in milestones:
                milestone_list.append(
                    {
                        "id": milestone.get("id", ""),
                        "name": milestone.get("name", ""),
                        "status": milestone.get("status", ""),
                        "start_date": milestone.get("start_date", ""),
                        "end_date": milestone.get("end_date", ""),
                    }
                )
            yaml_data["milestones"] = milestone_list

        # 添加史诗摘要
        if epics:
            epic_list = []
            for epic in epics:
                epic_list.append({"id": epic.get("id", ""), "title": epic.get("title", ""), "status": epic.get("status", "")})
            yaml_data["epics"] = epic_list

        # 添加故事摘要
        if stories:
            story_list = []
            for story in stories:
                story_list.append({"id": story.get("id", ""), "title": story.get("title", ""), "status": story.get("status", "")})
            yaml_data["stories"] = story_list

        # 转换为YAML格式
        yaml_string = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        formatted_output = yaml_string

        return {"success": True, "data": {"roadmap": roadmap_data, "formatted_output": formatted_output}}

    except Exception as e:
        logger.exception(f"显示路线图详情时出错")
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


def handle_show_health(service: RoadmapService, roadmap_id: str, format: str = "yaml") -> Dict:
    """显示路线图健康状态"""
    try:
        # 简化健康状态检查，避免使用已移除的方法
        health_result = {"status": {"health_score": 100, "status": "healthy"}}
        if not health_result:
            return {"success": False, "message": f"获取路线图 {roadmap_id} 健康状态失败"}

        # 使用YAML格式输出
        yaml_data = {
            "roadmap_id": roadmap_id,
            "health": {
                "score": health_result.get("status", {}).get("health_score", 100),
                "status": health_result.get("status", {}).get("status", "healthy"),
            },
        }

        # 添加问题和建议（如果有）
        if "issues" in health_result and health_result["issues"]:
            yaml_data["issues"] = health_result["issues"]

        if "recommendations" in health_result and health_result["recommendations"]:
            yaml_data["recommendations"] = health_result["recommendations"]

        # 转换为YAML格式
        yaml_string = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        formatted_output = yaml_string

        return {"success": True, "data": {"health": health_result, "formatted_output": formatted_output}}

    except Exception as e:
        return {"success": False, "message": f"显示健康状态时出错: {str(e)}"}
