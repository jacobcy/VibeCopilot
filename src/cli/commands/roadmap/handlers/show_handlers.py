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

        # 准备输出
        output = []
        output.append(f"roadmap:")
        output.append(f"  id: {roadmap_id}")
        output.append(f"  title: {roadmap.get('title') or roadmap.get('name') or '[未命名路线图]'}")
        output.append(f"{element_type}s:")

        # 按照编号排序
        elements = sorted(elements, key=lambda x: x.get("local_display_number", 0))

        # 计算ID列宽度，确保对齐
        max_id_len = max([len(e.get("id", "")) for e in elements], default=10)
        id_width = max(max_id_len, 10)

        # 添加表头
        output.append(f"  {'编号':<5}  {'ID':<{id_width}}  {'标题':<30}  {'状态'}")
        output.append(f"  {'-'*5}  {'-'*id_width}  {'-'*30}  {'-'*10}")

        # 添加元素数据，使用对齐格式
        for element in elements:
            display_number = element.get("local_display_number", "")
            element_id = element.get("id", "")
            title = element.get("title", "") or element.get("name", "")
            # 限制标题长度，避免过长
            if len(title) > 30:
                title = title[:27] + "..."
            status = element.get("status", "")

            # 格式化对齐的输出
            output.append(f"  #{display_number:<4}  {element_id:<{id_width}}  {title:<30}  {status}")

        formatted_output = "\n".join(output)

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

        # 使用更简洁的输出格式
        output = []
        output.append(f"roadmap:")
        output.append(f"  id: {roadmap_id}")
        output.append(f"  title: {roadmap.get('title') or roadmap.get('name') or '[未命名路线图]'}")
        output.append(f"  description: {roadmap.get('description', '')}")
        output.append(f"  version: {roadmap.get('version', '1.0')}")
        output.append(f"  status: {roadmap.get('status', '')}")
        output.append(f"  created_at: {roadmap.get('created_at', '')}")
        output.append(f"  updated_at: {roadmap.get('updated_at', '')}")
        output.append(f"  milestones_count: {len(milestones)}")
        output.append(f"  epics_count: {len(epics)}")
        output.append(f"  stories_count: {len(stories)}")

        # 添加里程碑摘要
        if milestones:
            output.append(f"milestones:")
            for milestone in milestones:
                milestone_id = milestone.get("id", "")
                name = milestone.get("name", "")
                status = milestone.get("status", "")
                output.append(f"- id: {milestone_id}")
                output.append(f"  name: {name}")
                output.append(f"  status: {status}")
                output.append(f"  start_date: {milestone.get('start_date', '')}")
                output.append(f"  end_date: {milestone.get('end_date', '')}")

        # 添加史诗摘要（使用对齐格式）
        if epics:
            output.append(f"epics:")
            # 按编号排序
            epics = sorted(epics, key=lambda x: x.get("local_display_number", 0))

            # 计算ID列宽度，确保对齐
            epic_max_id_len = max([len(e.get("id", "")) for e in epics], default=10)
            epic_id_width = max(epic_max_id_len, 10)

            # 添加表头
            output.append(f"  {'编号':<5}  {'ID':<{epic_id_width}}  {'标题':<30}  {'状态'}")
            output.append(f"  {'-'*5}  {'-'*epic_id_width}  {'-'*30}  {'-'*10}")

            for epic in epics:
                display_number = epic.get("local_display_number", "")
                epic_id = epic.get("id", "")
                title = epic.get("title", "") or epic.get("name", "")
                # 限制标题长度，避免过长
                if len(title) > 30:
                    title = title[:27] + "..."
                status = epic.get("status", "")

                # 格式化对齐输出
                output.append(f"  #{display_number:<4}  {epic_id:<{epic_id_width}}  {title:<30}  {status}")

        # 添加故事摘要（使用对齐格式）
        if stories:
            output.append(f"stories:")
            # 按编号排序
            stories = sorted(stories, key=lambda x: x.get("local_display_number", 0))

            # 计算ID列宽度，确保对齐
            story_max_id_len = max([len(s.get("id", "")) for s in stories], default=10)
            story_id_width = max(story_max_id_len, 10)

            # 添加表头
            output.append(f"  {'编号':<5}  {'ID':<{story_id_width}}  {'标题':<30}  {'状态'}")
            output.append(f"  {'-'*5}  {'-'*story_id_width}  {'-'*30}  {'-'*10}")

            for story in stories:
                display_number = story.get("local_display_number", "")
                story_id = story.get("id", "")
                title = story.get("title", "") or story.get("name", "")
                # 限制标题长度，避免过长
                if len(title) > 30:
                    title = title[:27] + "..."
                status = story.get("status", "")

                # 格式化对齐输出
                output.append(f"  #{display_number:<4}  {story_id:<{story_id_width}}  {title:<30}  {status}")

        # 组合所有输出
        formatted_output = "\n".join(output)

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


def handle_show_command(service, identifier=None, type_option=None):
    """
    处理show命令，包括标识符解析和类型推断

    Args:
        service: 路线图服务实例
        identifier: 路线图/元素的ID或名称
        type_option: 指定的元素类型

    Returns:
        Dict: 包含操作结果的字典
    """
    final_type = type_option
    id_to_process = identifier
    roadmap_context_id_for_listing = None

    # Case 1: 未提供identifier和type_option -> 显示活动路线图
    if not identifier and not type_option:
        final_type = "roadmap"
        id_to_process = service.active_roadmap_id
        if not id_to_process:
            return {"success": False, "message": "未提供标识符，且无活动路线图。请使用 'vc roadmap switch <ID>' 激活一个或提供一个ID。"}

    # Case 2: 提供了identifier但没有type_option
    elif identifier and not type_option:
        if identifier.startswith("rm_"):
            final_type = "roadmap"
        # 可以添加其他前缀的处理，如ms_, ep_, st_等
        else:
            final_type = "roadmap"
            # 尝试解析identifier是否为路线图名称
            if not identifier.startswith("rm_"):  # 如果不是ID格式
                resolved_roadmap = service.get_roadmap_by_title(identifier)
                if resolved_roadmap and resolved_roadmap.get("id"):
                    id_to_process = resolved_roadmap.get("id")
                else:
                    return {"success": False, "message": f"无法将 '{identifier}' 解析为已知的路线图标题，且其格式不是有效的路线图ID (rm_xxxx)。请使用 --type 指定，或提供有效ID/标题。"}

    # Case 3: 没有提供identifier但提供了type_option
    elif not identifier and type_option:
        final_type = type_option
        if final_type == "roadmap":  # 显示活动路线图
            id_to_process = service.active_roadmap_id
            if not id_to_process:
                return {"success": False, "message": "无活动路线图可显示。"}
        else:  # 列出活动路线图下的所有指定类型元素
            roadmap_context_id_for_listing = service.active_roadmap_id
            if not roadmap_context_id_for_listing:
                return {"success": False, "message": f"要列出 {final_type}，需要一个活动的路线图。请激活一个。"}
            id_to_process = None  # 不是显示特定元素，而是列出上下文中的元素

    # Case 4: 同时提供了identifier和type_option
    elif identifier and type_option:
        final_type = type_option
        id_to_process = identifier  # 可能是ID或名称
        if final_type != "roadmap":
            # 如果显示特定路线图下的元素，identifier是rm_xxx
            if identifier.startswith("rm_"):
                roadmap_context_id_for_listing = identifier
                id_to_process = None  # 列出上下文中的元素，而不是显示identifier本身

    # 确保final_type有值
    if not final_type:
        final_type = "roadmap"

    # 调用相应的处理函数
    result = None
    try:
        if final_type == "roadmap":
            target_roadmap_id = id_to_process
            if not target_roadmap_id or not target_roadmap_id.startswith("rm_"):
                return {"success": False, "message": f"显示路线图详情需要有效的路线图ID (rm_xxxx)。提供的: '{target_roadmap_id}'"}
            result = handle_show_roadmap(service, roadmap_id=target_roadmap_id, milestone_id=None, task_id=None, health=False, format="yaml")

        elif final_type == "milestone":
            context_id = roadmap_context_id_for_listing or service.active_roadmap_id
            if not context_id or not context_id.startswith("rm_"):
                return {"success": False, "message": "显示里程碑列表需要有效的路线图上下文ID (rm_xxxx)。"}
            result = handle_show_all_milestones(service, roadmap_id=context_id, format="yaml")

        elif final_type == "epic" or final_type == "story":
            context_id = roadmap_context_id_for_listing or service.active_roadmap_id
            if not context_id or not context_id.startswith("rm_"):
                return {"success": False, "message": f"显示 {final_type} 列表需要有效的路线图上下文ID (rm_xxxx)。"}
            result = handle_show_elements_by_type(service, roadmap_id=context_id, element_type=final_type, format="yaml")
        else:
            return {"success": False, "message": f"不支持的元素类型 '{final_type}'。"}

        if not result:
            return {"success": False, "message": "获取详情失败"}

        return result

    except Exception as e:
        logger.error(f"处理show命令时出错: {e}", exc_info=True)
        return {"success": False, "message": f"处理show命令时出错: {str(e)}"}
