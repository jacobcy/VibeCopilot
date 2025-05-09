"""
路线图数据模块

提供路线图数据获取相关功能，用于从数据库访问路线图数据。
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# 导入数据库相关
from sqlalchemy.orm import Session

from src.core.config import get_config  # 导入配置函数
from src.db.connection_manager import get_db_path, get_session
from src.db.repositories.roadmap_repository import RoadmapRepository
from src.db.session_manager import session_scope
from src.utils.id_generator import IdGenerator

if TYPE_CHECKING:
    from src.roadmap.service.roadmap_service import RoadmapService  # 循环导入保护

logger = logging.getLogger(__name__)


def get_roadmap(roadmap_id: str) -> Optional[Dict[str, Any]]:
    """获取单个路线图的字典表示"""
    from src.roadmap.service import RoadmapServiceFacade

    service = RoadmapServiceFacade()

    try:
        with session_scope() as session:
            roadmap_model = service.roadmap_repo.get_by_id(session, roadmap_id)
            if roadmap_model:
                return roadmap_model.to_dict()  # to_dict no longer includes github_link
            return None
    except Exception as e:
        logger.error(f"获取路线图 {roadmap_id} 时出错: {e}", exc_info=True)
        return None


def get_roadmaps() -> List[Dict[str, Any]]:
    """获取所有Roadmaps的列表，并包含更多调试信息"""
    from src.roadmap.service import RoadmapServiceFacade

    service = RoadmapServiceFacade()

    results = []
    db_path = get_db_path()
    logger.info(f"[get_roadmaps] Attempting to fetch roadmaps from DB: {db_path}")
    try:
        with session_scope() as session:
            roadmaps_entities = service.roadmap_repo.get_all(session)
            logger.info(f"[get_roadmaps] Fetched {len(roadmaps_entities) if roadmaps_entities else 0} entities from roadmap_repo.get_all()")
            if not roadmaps_entities:
                logger.info("[get_roadmaps] No roadmap entities found in the database via repository.")
                return []

            project_state = None
            try:
                from src.status.service import StatusService

                status_service = StatusService.get_instance()
                project_state = status_service.project_state
                logger.info("[get_roadmaps] Successfully obtained ProjectState.")
            except Exception as e:
                logger.warning(f"[get_roadmaps] Unable to get ProjectState: {e}", exc_info=True)

            active_id = None
            if project_state:
                try:
                    active_id = project_state.get_current_roadmap_id()
                    logger.info(f"[get_roadmaps] Active roadmap ID from ProjectState: {active_id}")
                except Exception as e:
                    logger.warning(f"[get_roadmaps] Error getting active_id from project_state: {e}", exc_info=True)
            else:
                logger.info("[get_roadmaps] ProjectState not available, active_id will be None.")

            for r in roadmaps_entities:
                try:
                    roadmap_dict = r.to_dict()
                    roadmap_dict["active"] = r.id == active_id
                    # Ensure stats are at least empty dict if not present
                    roadmap_dict.setdefault("stats", {})
                    results.append(roadmap_dict)
                except Exception as e_conv:
                    logger.error(
                        f"[get_roadmaps] Error converting roadmap entity (ID: {getattr(r, 'id', 'UNKNOWN')}) to dict: {e_conv}", exc_info=True
                    )

            logger.info(f"[get_roadmaps] Successfully processed {len(results)} roadmap entities into dicts.")

    except Exception as e:
        logger.error(f"[get_roadmaps] Error fetching roadmaps from database: {e}", exc_info=True)
        return []  # Return empty list on error to prevent further issues
    return results


def get_epics(roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取史诗列表"""
    from src.roadmap.service import RoadmapServiceFacade

    service = RoadmapServiceFacade()

    actual_roadmap_id = roadmap_id or service.active_roadmap_id
    if not actual_roadmap_id:
        logger.warning("get_epics: 未找到活动路线图ID")
        return []
    try:
        with session_scope() as session:
            epics_model = service.epic_repo.get_by_roadmap_id(session, actual_roadmap_id)
            return [epic.to_dict() for epic in epics_model]
    except Exception as e:
        logger.error(f"获取路线图 {actual_roadmap_id} 的史诗时出错: {e}", exc_info=True)
        return []


def get_stories(roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取用户故事列表"""
    from src.roadmap.service import RoadmapServiceFacade

    service = RoadmapServiceFacade()

    actual_roadmap_id = roadmap_id or service.active_roadmap_id
    if not actual_roadmap_id:
        logger.warning("get_stories: 未找到活动路线图ID")
        return []
    try:
        with session_scope() as session:
            stories_model = service.story_repo.get_by_roadmap_id(session, actual_roadmap_id)
            return [story.to_dict() for story in stories_model]
    except Exception as e:
        logger.error(f"获取路线图 {actual_roadmap_id} 的故事时出错: {e}", exc_info=True)
        return []


def get_milestones(roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取里程碑列表"""
    from src.roadmap.service import RoadmapServiceFacade

    service = RoadmapServiceFacade()

    actual_roadmap_id = roadmap_id or service.active_roadmap_id
    if not actual_roadmap_id:
        logger.warning("get_milestones: 未找到活动路线图ID")
        return []
    try:
        with session_scope() as session:
            milestones_model = service.milestone_repo.get_by_roadmap_id(session, actual_roadmap_id)
            if milestones_model:
                return [milestone.to_dict() for milestone in milestones_model]
            logger.info(f"未找到路线图 {actual_roadmap_id} 的里程碑，返回空列表")  # 更新日志
            return []
    except Exception as e:
        logger.error(f"获取路线图 {actual_roadmap_id} 的里程碑时出错: {e}", exc_info=True)
        return []


def get_milestone_tasks(milestone_id: str, roadmap_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取特定里程碑下的任务"""
    # roadmap_id 在这里可能用于验证里程碑是否属于该路线图，但基本查询只需要 milestone_id
    if not milestone_id:
        logger.warning("get_milestone_tasks: 未提供里程碑ID")
        return []
    try:
        return get_tasks(milestone_id=milestone_id)  # 复用get_tasks
    except Exception as e:
        logger.error(f"获取里程碑 {milestone_id} 的任务时出错: {e}", exc_info=True)
        return []


def get_tasks(roadmap_id: Optional[str] = None, milestone_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取任务列表，可按路线图或里程碑筛选"""
    from src.roadmap.service import RoadmapServiceFacade

    service = RoadmapServiceFacade()

    actual_roadmap_id = roadmap_id or service.active_roadmap_id
    if not actual_roadmap_id and not milestone_id:  # 如果都没有，则无法查询
        logger.warning("get_tasks: 路线图ID和里程碑ID均未提供")
        return []

    try:
        with session_scope() as session:
            if milestone_id:
                tasks_model = service.task_repo.get_by_milestone_id(session, milestone_id)
            elif actual_roadmap_id:  # 只有当milestone_id不存在时，才按roadmap_id查
                # TaskRepository 可能没有 get_by_roadmap_id, 需要通过milestone/story获取
                # 这是一个简化，实际可能需要更复杂的查询
                tasks_model = []
                milestones_in_roadmap = service.milestone_repo.get_by_roadmap_id(session, actual_roadmap_id)
                for milestone in milestones_in_roadmap:
                    tasks_model.extend(service.task_repo.get_by_milestone_id(session, milestone.id))
            else:  # 不应该到这里
                return []
            return [task.to_dict() for task in tasks_model]
    except Exception as e:
        logger.error(f"获取任务时出错 (roadmap_id: {actual_roadmap_id}, milestone_id: {milestone_id}): {e}", exc_info=True)
        return []


def _get_github_info(status_service=None) -> Dict[str, Any]:
    """
    获取GitHub相关信息。
    - owner 和 repo 从全局 GitHub 配置 (settings.json 通过 StatusService) 获取。
    - project_id 和 project_title 从当前活动路线图的后端配置 (ProjectState) 获取。
    """
    github_info_data = {}  # 用于存储最终结果

    # 1. 获取 StatusService 实例 (如果未提供)
    if not status_service:
        try:
            from src.roadmap.service.service_connector import get_status_service

            status_service = get_status_service()
            if not status_service:
                logger.error("未能获取StatusService实例 (在_get_github_info中)")
                raise ValueError("未能获取StatusService实例，请确保vc status init已经执行")
        except Exception as e:
            logger.error(f"获取StatusService实例时出错 (在_get_github_info中): {e}")
            raise ValueError(f"获取StatusService实例时出错，请确保vc status init已经执行: {e}")

    # 2. 从 StatusService 获取全局 GitHub owner 和 repo
    try:
        logger.info("尝试从StatusService获取全局GitHub owner/repo...")
        # GitHubInfoProvider.get_status() 直接返回包含 effective_owner/repo 的字典
        github_domain_status = status_service.get_domain_status("github_info")

        if github_domain_status and github_domain_status.get("configured", False):
            owner = github_domain_status.get("effective_owner")
            repo = github_domain_status.get("effective_repo")
            source = github_domain_status.get("source", "unknown")

            if not owner or not repo:
                logger.error(f"GitHub全局配置不完整，owner ({owner}) 或 repo ({repo}) 缺失。来源: {source}")
                raise ValueError("GitHub全局配置不完整 (owner/repo)，请执行 'vc status init' 命令配置GitHub信息")

            github_info_data["owner"] = owner
            github_info_data["repo"] = repo
            logger.info(f"从StatusService获取全局GitHub信息成功: {owner}/{repo} (来源: {source})")
        else:
            status_message = github_domain_status.get("status_message", "GitHub未配置或获取失败")
            logger.error(f"GitHub全局配置未就绪或获取失败: {status_message}")
            raise ValueError(f"GitHub全局配置未就绪: {status_message}。请执行 'vc status init'。")

    except Exception as e:
        if isinstance(e, ValueError) and ("请执行 'vc status init'" in str(e) or "全局配置不完整" in str(e)):
            raise
        logger.error(f"从StatusService获取全局GitHub owner/repo时出错: {e}", exc_info=True)
        raise ValueError(f"获取全局GitHub owner/repo失败: {e}。请执行 'vc status init'。")

    # 3. 从 ProjectState 获取当前活动路线图的 project_id 和 project_title
    try:
        project_state = status_service.project_state
        active_gh_config = project_state.get_active_roadmap_backend_config().get("github", {})

        project_id = active_gh_config.get("project_id")
        project_title = active_gh_config.get("project_title")  # 可能是 None

        github_info_data["project_id"] = project_id  # 允许为 None
        github_info_data["project_title"] = project_title  # 允许为 None

        logger.info(f"从ProjectState获取活动路线图的GitHub Project信息: ID={project_id}, Title={project_title}")

    except Exception as e:
        logger.warning(f"从ProjectState获取活动GitHub Project信息时出错: {e}。project_id 和 project_title 可能未设置。", exc_info=True)
        github_info_data["project_id"] = None  # 确保在出错时这些键存在且为None
        github_info_data["project_title"] = None

    # roadmap_title 在这个上下文中似乎与 project_title 重复或不明确，暂时移除
    # 如果需要一个通用的项目标题，可以考虑从 project_state.get_project_name() 获取
    # github_info_data["roadmap_title"] = project_title or "VibeCopilot Project"

    return github_info_data


def get_roadmap_info(roadmap_id: Optional[str] = None) -> Dict[str, Any]:
    """获取路线图详细信息，包括关联的Epic、Story、任务等"""
    from src.roadmap.service import RoadmapServiceFacade

    service = RoadmapServiceFacade()

    # 尝试获取路线图信息
    actual_roadmap_id = roadmap_id or service.active_roadmap_id
    if not actual_roadmap_id:
        logger.warning("get_roadmap_info: 未找到活动路线图ID")
        return {}

    try:
        # 获取路线图基本信息
        roadmap_info = get_roadmap(actual_roadmap_id) or {}
        if not roadmap_info:
            logger.warning(f"未找到路线图: {actual_roadmap_id}")
            return {}

        # 获取统计数据
        epics_list = get_epics(actual_roadmap_id)
        milestones_list = get_milestones(actual_roadmap_id)
        stories_list = get_stories(actual_roadmap_id)

        total_tasks = 0
        completed_tasks = 0
        for milestone in milestones_list:
            milestone_tasks = get_milestone_tasks(milestone.get("id", ""), actual_roadmap_id)
            total_tasks += len(milestone_tasks)
            completed_tasks += sum(1 for task in milestone_tasks if task.get("status") == "completed")

        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        stats = {
            "total_epics": len(epics_list),
            "total_milestones": len(milestones_list),
            "total_stories": len(stories_list),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress": round(progress, 2),
        }
        logger.debug(f"[roadmap_data.get_roadmap_info] stats: {stats}")

        # 添加 GitHub 链接信息 (与 patch 逻辑对齐)
        if not roadmap_info.get("github_link"):
            try:
                from src.status.service import StatusService  # 确保导入

                status_service = StatusService.get_instance()
                project_state = status_service.project_state

                # 检查是否有 GitHub 项目链接
                github_project_id = project_state.get_github_project_id_for_roadmap(actual_roadmap_id)
                if github_project_id:
                    # 从 settings.json 获取 owner/repo
                    github_info = status_service.get_domain_status("github_info") or {}
                    owner = github_info.get("effective_owner")
                    repo = github_info.get("effective_repo")

                    if owner and repo and github_project_id:
                        # 构建 GitHub 链接
                        project_id_str = str(github_project_id) if github_project_id.isdigit() else github_project_id
                        github_link_data = {
                            "owner": owner,
                            "repo": repo,
                            "project_id": project_id_str,
                            "url": f"https://github.com/{owner}/{repo}/projects/{project_id_str}",
                        }
                        roadmap_info["github_link"] = github_link_data
                        logger.info(f"已添加 GitHub 链接信息: {github_link_data}")
                    else:
                        logger.warning(f"缺少构建 GitHub 链接所需的信息: owner={owner}, repo={repo}, project_id={github_project_id}")
            except Exception as e:
                logger.error(f"添加 GitHub 链接时出错: {e}", exc_info=True)

        # 确保路线图名称存在
        if roadmap_info and not roadmap_info.get("name") and roadmap_info.get("title"):
            roadmap_info["name"] = roadmap_info.get("title")

        # 构建最终结果
        final_result = {
            "success": True,
            "roadmap": roadmap_info,
            "stats": stats,
            "name": roadmap_info.get("name", "未命名路线图") if roadmap_info else "未命名路线图",
            "description": roadmap_info.get("description", "无描述") if roadmap_info else "无描述",
            "active_id": service.active_roadmap_id,
        }

        return final_result

    except Exception as e:
        logger.error(f"获取路线图详情时出错: {e}", exc_info=True)
        return {"success": False, "error": f"获取路线图详情时出错: {e}"}
