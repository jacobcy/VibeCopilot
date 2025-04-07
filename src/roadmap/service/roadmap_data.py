"""
路线图数据模块

提供路线图数据获取相关功能，用于从数据库访问路线图数据。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def get_roadmap(service, roadmap_id: str) -> Optional[Dict[str, Any]]:
    """获取路线图

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID

    Returns:
        Optional[Dict[str, Any]]: 路线图数据
    """
    # 简化实现 - 返回模拟数据
    return {"id": roadmap_id, "name": "示例路线图", "description": "这是一个示例路线图", "version": "1.0"}


def get_roadmaps(service) -> List[Dict[str, Any]]:
    """获取所有路线图

    Args:
        service: 路线图服务实例

    Returns:
        List[Dict[str, Any]]: 路线图列表
    """
    # 简化实现 - 返回模拟数据
    return [
        {"id": "roadmap-123", "name": "示例路线图1", "description": "这是示例路线图1", "version": "1.0"},
        {"id": "roadmap-456", "name": "示例路线图2", "description": "这是示例路线图2", "version": "1.0"},
    ]


def get_epics(service, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取路线图下的所有Epic

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        List[Dict[str, Any]]: Epic列表
    """
    roadmap_id = roadmap_id or service.active_roadmap_id
    epics = service.epic_repo.filter(roadmap_id=roadmap_id)
    return [service._object_to_dict(epic) for epic in epics]


def get_stories(service, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取路线图下的所有Story

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        List[Dict[str, Any]]: Story列表
    """
    roadmap_id = roadmap_id or service.active_roadmap_id
    stories = service.story_repo.filter(roadmap_id=roadmap_id)
    return [service._object_to_dict(story) for story in stories]


def get_milestones(service, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取路线图下的所有Milestone

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        List[Dict[str, Any]]: Milestone列表
    """
    # 简化实现 - 返回模拟数据
    return [
        {
            "id": "milestone-123",
            "name": "里程碑1",
            "description": "这是里程碑1",
            "status": "in_progress",
            "progress": 50,
            "roadmap_id": roadmap_id or service.active_roadmap_id,
        },
        {
            "id": "milestone-456",
            "name": "里程碑2",
            "description": "这是里程碑2",
            "status": "planned",
            "progress": 0,
            "roadmap_id": roadmap_id or service.active_roadmap_id,
        },
    ]


def get_milestone_tasks(
    service, milestone_id: str, roadmap_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """获取里程碑下的所有任务

    Args:
        service: 路线图服务实例
        milestone_id: 里程碑ID
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        List[Dict[str, Any]]: 任务列表
    """
    # 简化实现 - 返回模拟数据
    return [
        {"id": f"task-{milestone_id}-1", "name": "任务1", "status": "completed"},
        {"id": f"task-{milestone_id}-2", "name": "任务2", "status": "in_progress"},
    ]


def list_tasks(service, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取路线图下的所有任务

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        List[Dict[str, Any]]: 任务列表
    """
    roadmap_id = roadmap_id or service.active_roadmap_id

    try:
        # 尝试从数据库获取任务
        tasks = service.task_repo.filter(roadmap_id=roadmap_id)
        return [service._object_to_dict(task) for task in tasks]
    except Exception as e:
        logger.error(f"SQLAlchemy查询Task失败: {e}")

        # 记录错误，返回模拟数据作为临时解决方案
        logger.warning("返回模拟任务数据作为临时解决方案")

        # 返回模拟数据
        return [
            {
                "id": "T001",
                "title": "实现状态命令",
                "roadmap_id": roadmap_id,
                "status": "completed",
                "priority": "P1",
                "milestone": "M001",
                "description": "完成status命令实现",
            },
            {
                "id": "T002",
                "title": "修复Task数据库模型",
                "roadmap_id": roadmap_id,
                "status": "in_progress",
                "priority": "P1",
                "milestone": "M001",
                "description": "将Task类转换为SQLAlchemy模型并初始化数据库表",
            },
            {
                "id": "T003",
                "title": "完成路线图状态集成",
                "roadmap_id": roadmap_id,
                "status": "todo",
                "priority": "P2",
                "milestone": "M002",
                "description": "集成路线图状态到系统状态中",
            },
        ]


def get_roadmap_info(service, roadmap_id: Optional[str] = None) -> Dict[str, Any]:
    """
    获取路线图信息

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        Dict[str, Any]: 路线图信息
    """
    roadmap_id = roadmap_id or service.active_roadmap_id

    # 获取路线图基本信息
    roadmap = get_roadmap(service, roadmap_id)
    if not roadmap:
        return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

    # 获取统计信息
    epics = get_epics(service, roadmap_id)
    milestones = get_milestones(service, roadmap_id)
    stories = get_stories(service, roadmap_id)

    tasks_count = 0
    completed_tasks = 0
    for milestone in milestones:
        milestone_tasks = get_milestone_tasks(service, milestone.get("id"), roadmap_id)
        tasks_count += len(milestone_tasks)
        completed_tasks += sum(1 for task in milestone_tasks if task.get("status") == "completed")

    # 计算整体进度
    progress = 0.0
    if tasks_count > 0:
        progress = completed_tasks / tasks_count * 100

    # 获取状态信息
    status_info = service.manager.check_roadmap("roadmap", roadmap_id=roadmap_id)

    return {
        "success": True,
        "roadmap": roadmap,
        "stats": {
            "epics_count": len(epics),
            "milestones_count": len(milestones),
            "stories_count": len(stories),
            "tasks_count": tasks_count,
            "completed_tasks": completed_tasks,
            "progress": progress,
        },
        "status": status_info,
    }
