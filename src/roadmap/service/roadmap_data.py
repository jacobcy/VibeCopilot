"""
路线图数据模块

提供路线图数据获取相关功能，用于从数据库访问路线图数据。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.db.repositories.roadmap_repository import RoadmapRepository
from src.db.session_manager import session_scope

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
        # 使用 session_scope 获取会话
        with session_scope() as session:
            # 使用 service 上的无状态 repo，并传入 session 和 id
            roadmap = service.roadmap_repo.get_by_id(session, roadmap_id)
            if roadmap:
                # 确保 service._object_to_dict 是可用的
                return service._object_to_dict(roadmap)
            # 如果在 session 内未找到 roadmap
            else:
                logger.warning(f"在数据库会话内未找到路线图: {roadmap_id}")
                # 这里可以返回 None，或者让函数继续执行到下面的 return None
                # 为清晰起见，让它继续
                pass

    except Exception as e:
        # 如果在数据库操作过程中出错
        logger.error(f"获取路线图时数据库操作失败: {e}", exc_info=True)
        return None  # 出错则返回 None

    # 如果 try 块成功执行完毕但没有在 if roadmap 中返回 (即 roadmap 未找到)
    logger.warning(f"获取路线图完成，但未找到: {roadmap_id}")
    return None


def get_roadmaps(service) -> List[Dict[str, Any]]:
    """获取所有路线图

    Args:
        service: 路线图服务实例

    Returns:
        List[Dict[str, Any]]: 路线图列表
    """
    try:
        # 使用 session_scope 并调用无状态 repo
        with session_scope() as session:
            # 移除旧的仓库实例化
            # roadmap_repo = RoadmapRepository(session)
            # 调用 service 上的无状态 repo，并传入 session
            roadmaps = service.roadmap_repo.get_all(session)
            if roadmaps:
                # 确保 service._object_to_dict 是可用的
                return [service._object_to_dict(roadmap) for roadmap in roadmaps]

            # 如果没有路线图，返回空列表
            logger.info("数据库中没有找到路线图，返回空列表")
            return []
    except Exception as e:
        # 如果出错，记录错误并返回空列表
        logger.error(f"获取路线图列表失败: {e}", exc_info=True)  # 添加 exc_info
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
    if not roadmap_id:
        logger.error("未设置活跃路线图，无法获取 Epic")
        return []
    try:
        # --- 使用 session_scope ---
        with session_scope() as session:
            # 调用 repo 的 get_by_roadmap_id 方法
            epics = service.epic_repo.get_by_roadmap_id(session, roadmap_id)
            return [service._object_to_dict(epic) for epic in epics]
        # ------------------------
    except Exception as e:
        logger.error(f"获取路线图 Epics 失败 (ID: {roadmap_id}): {e}", exc_info=True)
        return []


def get_stories(service, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取路线图下的所有Story

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        List[Dict[str, Any]]: Story列表
    """
    roadmap_id = roadmap_id or service.active_roadmap_id
    if not roadmap_id:
        logger.error("未设置活跃路线图，无法获取 Story")
        return []
    try:
        # --- 使用 session_scope ---
        with session_scope() as session:
            # 调用 repo 的 get_by_roadmap_id 方法
            stories = service.story_repo.get_by_roadmap_id(session, roadmap_id)
            return [service._object_to_dict(story) for story in stories]
        # ------------------------
    except Exception as e:
        logger.error(f"获取路线图 Stories 失败 (ID: {roadmap_id}): {e}", exc_info=True)
        return []


def get_milestones(service, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取路线图下的所有Milestone

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        List[Dict[str, Any]]: Milestone列表
    """
    roadmap_id = roadmap_id or service.active_roadmap_id
    if not roadmap_id:
        logger.error("未设置活跃路线图，无法获取里程碑")
        return []

    try:
        # 使用 session_scope 获取会话
        with session_scope() as session:
            # 移除旧的检查和实例化逻辑
            # milestone_repo = service.milestone_repo
            # if milestone_repo is None:
            #     from src.db.repositories.roadmap_repository import MilestoneRepository
            #     milestone_repo = MilestoneRepository(service.session) # 错误：访问 service.session

            # 调用无状态 repo，传入 session
            milestones = service.milestone_repo.filter(session, roadmap_id=roadmap_id)
            if milestones:
                return [service._object_to_dict(milestone) for milestone in milestones]

        # 如果未找到
        logger.info(f"未找到路线图 {roadmap_id} 的里程碑，返回空列表")
        return []
    except Exception as e:
        logger.error(f"获取路线图里程碑失败: {e}", exc_info=True)  # 添加 exc_info
        return []


def get_milestone_tasks(service, milestone_id: str, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取里程碑下的所有任务 (注意：Task 不能直接关联 Milestone)

    Args:
        service: 路线图服务实例
        milestone_id: 里程碑ID
        roadmap_id: 路线图ID，不提供则使用活跃路线图

    Returns:
        List[Dict[str, Any]]: 任务列表
    """
    # roadmap_id = roadmap_id or service.active_roadmap_id # roadmap_id 在此逻辑中可能不是必需的

    # --- 由于 Task 不能直接关联 Milestone，此函数逻辑需要重审 ---
    logger.warning(f"get_milestone_tasks 调用 (Milestone ID: {milestone_id})，但 Task 模型无法直接关联 Milestone。此函数可能返回空或需要调整逻辑。")
    # 可能的替代逻辑：
    # 1. 找到 Milestone 关联的 Epics/Stories (如果模型支持)
    # 2. 找到这些 Stories 下的 Tasks
    # 或者，如果业务逻辑允许 Task 有一个 milestone_id 字段（当前没有），则修改模型和查询

    # 暂时返回空列表，表示无法按此方式获取
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
    if not roadmap_id and not milestone_id:
        logger.error("未设置活跃路线图且未提供里程碑ID，无法获取任务")
        return []

    try:
        tasks_dicts = []  # Initialize list for dictionaries
        with session_scope() as session:  # Open session scope
            tasks = []
            if milestone_id:
                # --- 注意: Task 模型当前没有直接的 milestone_id 关联 --- #
                # 这部分逻辑可能需要调整或依赖 TaskRepository 的 filter 实现
                logger.warning(f"Fetching tasks by milestone_id ({milestone_id}), which might not be directly supported by Task model.")
                milestone_tasks = service.task_repo.filter(session, milestone_id=milestone_id)
                if milestone_tasks:
                    tasks.extend(milestone_tasks)
            elif roadmap_id:
                # --- 获取与路线图关联的任务 (通过 Story -> Epic -> Roadmap) --- #
                # 假设 TaskRepository.get_by_roadmap_id 实现了正确的关联查询
                roadmap_tasks = service.task_repo.get_by_roadmap_id(session, roadmap_id)
                # --- 添加日志 ---
                logger.debug(f"[get_tasks] Fetched {len(roadmap_tasks)} raw task objects for roadmap {roadmap_id} from repository.")
                if roadmap_tasks:
                    tasks.extend(roadmap_tasks)
                    logger.info(f"从路线图 {roadmap_id} 找到 {len(tasks)} 个任务")
                else:
                    logger.info(f"路线图 {roadmap_id} 下未找到任务")

            # --- Convert to dicts *inside* the session scope --- #
            if tasks:
                for task in tasks:
                    task_dict = {
                        "id": task.id,
                        "title": task.title,  # Explicitly include title
                        "description": task.description,
                        "status": task.status,  # Directly use the string value
                        "priority": task.priority,  # Directly use the string value
                        "story_id": task.story_id,
                        "story_title": task.story.title if task.story else "N/A",  # Include story title
                        "created_at": task.created_at if task.created_at else None,  # Directly use the string value
                        "updated_at": task.updated_at if task.updated_at else None  # Directly use the string value
                        # Add other necessary fields from Task model if needed
                    }
                    tasks_dicts.append(task_dict)

            # --- 添加日志 ---
            logger.debug(f"[get_tasks] Returning {len(tasks_dicts)} task dictionaries for roadmap {roadmap_id}.")
            # Session closes here

        # --- Return the list of dictionaries outside the scope --- #
        if not tasks_dicts:
            params_str = f"路线图ID={roadmap_id}" if roadmap_id else ""
            params_str += f"{', ' if params_str else ''}里程碑ID={milestone_id}" if milestone_id else ""
            logger.info(f"未找到{params_str}的任务，返回空列表")

        return tasks_dicts

    except Exception as e:
        logger.error(f"获取任务失败: {e}", exc_info=True)
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
