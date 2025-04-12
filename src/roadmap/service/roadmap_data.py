"""
路线图数据模块

提供路线图数据获取相关功能，用于从数据库访问路线图数据。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.db.repositories.roadmap_repository import RoadmapRepository

logger = logging.getLogger(__name__)


def get_roadmap(service, roadmap_id: str) -> Optional[Dict[str, Any]]:
    """获取路线图

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID

    Returns:
        Optional[Dict[str, Any]]: 路线图数据
    """
    try:
        # 从数据库获取路线图
        roadmap_repo = service.roadmap_repo
        if roadmap_repo is None:
            from src.db.repositories.roadmap_repository import RoadmapRepository

            roadmap_repo = RoadmapRepository(service.session)

        roadmap = roadmap_repo.get_by_id(roadmap_id)
        if roadmap:
            return service._object_to_dict(roadmap)

        # 如果没有找到，返回None
        logger.warning(f"未找到路线图: {roadmap_id}")
        return None
    except Exception as e:
        # 如果出错，记录错误并返回None
        logger.error(f"获取路线图失败: {e}")
        return None


def get_roadmaps(service) -> List[Dict[str, Any]]:
    """获取所有路线图

    Args:
        service: 路线图服务实例

    Returns:
        List[Dict[str, Any]]: 路线图列表
    """
    try:
        # 从数据库获取所有路线图
        with service.session_factory() as session:
            roadmap_repo = RoadmapRepository(session)
            roadmaps = roadmap_repo.get_all()
            if roadmaps:
                return [service._object_to_dict(roadmap) for roadmap in roadmaps]

            # 如果没有路线图，返回空列表
            logger.info("数据库中没有找到路线图，返回空列表")
            return []
    except Exception as e:
        # 如果出错，记录错误并返回空列表
        logger.error(f"获取路线图列表失败: {e}")
        return []


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
    roadmap_id = roadmap_id or service.active_roadmap_id

    # 如果依然没有roadmap_id，记录错误并返回空列表
    if not roadmap_id:
        logger.error("未设置活跃路线图，无法获取里程碑")
        return []

    try:
        # 从数据库获取里程碑
        milestone_repo = service.milestone_repo
        if milestone_repo is None:
            from src.db.repositories.roadmap_repository import MilestoneRepository

            milestone_repo = MilestoneRepository(service.session)

        milestones = milestone_repo.filter(roadmap_id=roadmap_id)
        if milestones:
            return [service._object_to_dict(milestone) for milestone in milestones]

        # 如果没有找到，记录并返回空列表
        logger.info(f"未找到路线图 {roadmap_id} 的里程碑，返回空列表")
        return []
    except Exception as e:
        # 如果出错，记录错误并返回空列表
        logger.error(f"获取路线图里程碑失败: {e}")
        return []


def get_milestone_tasks(service, milestone_id: str, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取里程碑下的所有任务

    Args:
        service: 路线图服务实例
        milestone_id: 里程碑ID
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        List[Dict[str, Any]]: 任务列表
    """
    roadmap_id = roadmap_id or service.active_roadmap_id

    try:
        # 从数据库获取与里程碑关联的任务
        tasks = service.task_repo.search_tasks(roadmap_item_id=milestone_id)

        if tasks:
            return [service._object_to_dict(task) for task in tasks]

        # 如果没有找到，记录并返回空列表
        logger.info(f"未找到里程碑 {milestone_id} 的任务，返回空列表")
        return []
    except Exception as e:
        # 如果出错，记录错误并返回空列表
        logger.error(f"获取里程碑任务失败: {e}")
        return []


def get_tasks(service, roadmap_id: Optional[str] = None, milestone_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取路线图或里程碑下的所有Task

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图
        milestone_id: 里程碑ID，如果提供则获取特定里程碑下的任务

    Returns:
        List[Dict[str, Any]]: Task列表
    """
    roadmap_id = roadmap_id or service.active_roadmap_id

    # 如果依然没有roadmap_id且没有milestone_id，记录错误并返回空列表
    if not roadmap_id and not milestone_id:
        logger.error("未设置活跃路线图且未提供里程碑ID，无法获取任务")
        return []

    try:
        # 从数据库获取任务
        task_repo = service.task_repo
        if task_repo is None:
            from src.db.repositories.roadmap_repository import TaskRepository

            task_repo = TaskRepository(service.session)

        tasks = []
        if milestone_id:
            # 使用里程碑ID过滤
            milestone_tasks = task_repo.filter(milestone_id=milestone_id)
            if milestone_tasks:
                tasks.extend(milestone_tasks)
        elif roadmap_id:
            # 使用roadmap_id应该调用特定方法而不是filter
            # 因为Task和Roadmap的关系是通过Story和Epic间接建立的
            tasks = task_repo.get_by_roadmap_id(roadmap_id)
            logger.info(f"从路线图 {roadmap_id} 找到 {len(tasks)} 个任务")

        if tasks:
            return [service._object_to_dict(task) for task in tasks]

        # 如果没有找到，记录并返回空列表
        params_str = f"路线图ID={roadmap_id}" if roadmap_id else ""
        params_str += f"{', ' if params_str else ''}里程碑ID={milestone_id}" if milestone_id else ""
        logger.info(f"未找到{params_str}的任务，返回空列表")
        return []
    except Exception as e:
        # 如果出错，记录错误并返回空列表
        logger.error(f"获取任务失败: {e}")
        return []


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
