"""
路线图模板管理模块

提供路线图模板的获取和应用功能。
"""

from typing import Any, Dict, List


def get_roadmap_template(template_name: str = "default") -> Dict[str, Any]:
    """
    获取指定的路线图模板

    Args:
        template_name: 模板名称

    Returns:
        Dict[str, Any]: 模板数据
    """
    templates = {
        "default": {
            "milestones": [
                {"name": "规划", "duration": 14},
                {"name": "开发", "duration": 30},
                {"name": "测试", "duration": 14},
                {"name": "发布", "duration": 7},
            ],
            "task_statuses": ["todo", "in_progress", "review", "completed"],
            "priorities": ["P0", "P1", "P2", "P3"],
        },
        "agile": {
            "milestones": [
                {"name": "Sprint 1", "duration": 14},
                {"name": "Sprint 2", "duration": 14},
                {"name": "Sprint 3", "duration": 14},
                {"name": "Release", "duration": 7},
            ],
            "task_statuses": ["backlog", "todo", "in_progress", "review", "done"],
            "priorities": ["critical", "high", "medium", "low"],
        },
        "minimal": {
            "milestones": [
                {"name": "计划", "duration": 7},
                {"name": "执行", "duration": 21},
                {"name": "完成", "duration": 7},
            ],
            "task_statuses": ["todo", "doing", "done"],
            "priorities": ["high", "medium", "low"],
        },
    }

    return templates.get(template_name, templates["default"])


def apply_template(data: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """
    将模板应用于路线图数据

    Args:
        data: 原始路线图数据
        template: 要应用的模板

    Returns:
        Dict[str, Any]: 应用模板后的路线图数据
    """
    result = data.copy()

    # 如果没有里程碑，则应用模板里程碑
    if not result.get("milestones"):
        result["milestones"] = _generate_milestones_from_template(template)

    # 确保任务状态一致
    if "tasks" in result:
        result["tasks"] = _normalize_task_statuses(
            result["tasks"], template.get("task_statuses", [])
        )

    # 确保优先级一致
    if "tasks" in result:
        result["tasks"] = _normalize_priorities(result["tasks"], template.get("priorities", []))

    return result


def _generate_milestones_from_template(template: Dict[str, Any]) -> List[Dict[str, Any]]:
    """根据模板生成里程碑"""
    milestones = []
    for i, m in enumerate(template.get("milestones", [])):
        milestone = {
            "id": f"m-{i+1}",
            "name": m.get("name", f"Milestone {i+1}"),
            "duration": m.get("duration", 14),
            # 其他字段可以根据需要添加
        }
        milestones.append(milestone)
    return milestones


def _normalize_task_statuses(
    tasks: List[Dict[str, Any]], valid_statuses: List[str]
) -> List[Dict[str, Any]]:
    """确保任务状态在有效范围内"""
    if not valid_statuses:
        return tasks

    result = []
    for task in tasks:
        task_copy = task.copy()
        if "status" in task_copy and task_copy["status"] not in valid_statuses:
            # 选择一个合适的替代状态
            if task_copy["status"] in ["done", "completed", "complete"]:
                task_copy["status"] = valid_statuses[-1]  # 假设最后一个是完成状态
            else:
                task_copy["status"] = valid_statuses[0]  # 默认使用第一个状态
        result.append(task_copy)
    return result


def _normalize_priorities(
    tasks: List[Dict[str, Any]], valid_priorities: List[str]
) -> List[Dict[str, Any]]:
    """确保任务优先级在有效范围内"""
    if not valid_priorities:
        return tasks

    result = []
    for task in tasks:
        task_copy = task.copy()
        if "priority" in task_copy and task_copy["priority"] not in valid_priorities:
            # 选择一个中等优先级
            middle_index = len(valid_priorities) // 2
            task_copy["priority"] = valid_priorities[middle_index]
        result.append(task_copy)
    return result
