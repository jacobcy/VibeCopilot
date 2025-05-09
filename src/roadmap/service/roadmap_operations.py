"""
路线图操作模块

提供路线图的创建、更新、删除功能，以及其他复杂的操作封装。
"""

import logging
from typing import Any, Dict, List, Optional

from src.db.session_manager import session_scope

# 导入数据层函数，供 switch_active_roadmap 使用
from src.roadmap.service.roadmap_data import get_roadmap

logger = logging.getLogger(__name__)


def delete_roadmap(service, roadmap_id: str) -> Dict[str, Any]:
    """
    删除路线图

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID

    Returns:
        Dict[str, Any]: 删除结果
    """
    try:
        # 检查路线图是否存在 - 使用 session
        with session_scope() as session:
            roadmap_obj = service.roadmap_repo.get_by_id(session, roadmap_id)
            if not roadmap_obj:
                return {"success": False, "error": f"未找到路线图: {roadmap_id}"}
            roadmap_name = roadmap_obj.title  # Get name before potential deletion

        # 检查是否是活跃路线图 (在 session 外检查，避免持有 session)
        active_id = service.active_roadmap_id
        if roadmap_id == active_id:
            return {"success": False, "error": "不能删除当前活跃路线图，请先切换到其他路线图"}

        # 删除路线图及其所有内容 - 使用 session
        try:
            with session_scope() as session:
                # 调用 delete 时传递 session 和 id
                deleted = service.roadmap_repo.delete(session, roadmap_id)
                if deleted:
                    logger.info(f"删除路线图: {roadmap_name} (ID: {roadmap_id})")
                    return {"success": True, "roadmap_id": roadmap_id, "roadmap_name": roadmap_name}
                else:
                    # Repository delete should return False if not found, but we checked above
                    logger.warning(f"尝试删除路线图 {roadmap_id} 时，delete 方法返回 False。")
                    return {"success": False, "error": "删除路线图失败 (Repository 返回 False)"}
        except Exception as e:
            logger.error(f"删除路线图时数据库操作出错: {e}", exc_info=True)
            return {"success": False, "error": f"数据库错误: {str(e)}"}

    except Exception as e:
        logger.error(f"删除路线图前检查时出错: {e}", exc_info=True)
        return {"success": False, "error": f"检查路线图时出错: {str(e)}"}


def switch_active_roadmap(service, roadmap_id: str) -> Dict[str, Any]:
    """
    切换当前活跃路线图 (操作层实现)

    Args:
        service: 路线图服务实例
        roadmap_id: 路线图ID

    Returns:
        Dict[str, Any]: 切换结果
    """
    try:
        # 检查路线图是否存在 (调用数据层)
        roadmap_dict = get_roadmap(service, roadmap_id)
        if not roadmap_dict:
            return {"success": False, "error": f"未找到路线图: {roadmap_id}"}

        # 调用 service 的 set_active_roadmap 持久化设置
        # service.set_active_roadmap 负责调用 status_provider
        success = service.set_active_roadmap(roadmap_id)
        if not success:
            return {"success": False, "error": f"切换路线图失败: {roadmap_id}"}

        # 优先使用title字段，然后是name字段
        roadmap_name = roadmap_dict.get("title") or roadmap_dict.get("name") or "[未命名路线图]"
        logger.info(f"切换到路线图: {roadmap_name} (ID: {roadmap_id})")
        return {"success": True, "roadmap_id": roadmap_id, "roadmap_name": roadmap_name}

    except Exception as e:
        logger.error(f"切换路线图出错: {e}")
        return {"success": False, "error": f"切换路线图出错: {str(e)}"}


def list_roadmap_elements(
    service,
    type: str = "all",
    status: str = "all",
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    sort_by: str = "id",
    sort_desc: bool = False,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """列出路线图元素 (操作层实现)

    Args:
        service: 路线图服务实例
        type: 元素类型，可选 'all', 'milestone', 'story', 'task'
        status: 筛选状态
        assignee: 筛选指派人
        labels: 筛选标签列表
        sort_by: 排序字段
        sort_desc: 是否降序排序
        page: 页码
        page_size: 每页数量

    Returns:
        Dict[str, Any]: 查询结果
    """
    try:
        # 获取活动路线图
        roadmap_id = service.active_roadmap_id
        if not roadmap_id:
            return {"success": False, "message": "未设置活动路线图", "data": [], "total": 0}

        # 根据类型获取元素
        elements = []
        with session_scope() as session:
            if type == "all" or type == "milestone":
                milestones = service.milestone_repo.get_by_roadmap_id(session, roadmap_id)
                for milestone in milestones:
                    milestone_status = str(milestone.status) if milestone.status is not None else ""
                    if status != "all" and milestone_status != status:
                        continue
                    elements.append(
                        {
                            "id": milestone.id,
                            "type": "milestone",
                            "name": milestone.title,
                            "title": milestone.title,
                            "status": milestone.status,
                            "priority": "normal",
                            "assignee": "",
                            "labels": [],
                        }
                    )

            if type == "all" or type == "story":
                stories = service.story_repo.get_by_roadmap_id(session, roadmap_id)
                for story in stories:
                    story_status = str(story.status) if story.status is not None else ""
                    if status != "all" and story_status != status:
                        continue
                    story_labels = getattr(story, "labels", "").split(",") if hasattr(story, "labels") else []
                    if labels and not any(label in story_labels for label in labels):
                        continue
                    elements.append(
                        {
                            "id": story.id,
                            "type": "story",
                            "name": story.title,
                            "title": story.title,
                            "status": story.status,
                            "priority": story.priority,
                            "labels": story_labels,
                        }
                    )

            if type == "all" or type == "task":
                tasks = service.task_repo.get_by_roadmap_id(session, roadmap_id)
                for task in tasks:
                    task_status = str(task.status) if task.status is not None else ""
                    if status != "all" and task_status != status:
                        continue
                    task_assignee = str(task.assignee) if task.assignee is not None else ""
                    if assignee and task_assignee != assignee:
                        continue
                    task_labels_value = task.labels
                    if isinstance(task_labels_value, list):
                        task_labels = task_labels_value
                    else:
                        task_labels_str = str(task_labels_value) if task_labels_value is not None else ""
                        task_labels = task_labels_str.split(",") if task_labels_str else []
                    if labels and not any(label in task_labels for label in labels):
                        continue
                    elements.append(
                        {
                            "id": task.id,
                            "type": "task",
                            "name": task.title,
                            "title": task.title,
                            "status": task.status,
                            "priority": task.priority,
                            "assignee": task.assignee,
                            "labels": task_labels,
                        }
                    )

        # 排序
        if sort_by in ["id", "title", "status", "priority"]:
            elements.sort(key=lambda x: x.get(sort_by, ""), reverse=sort_desc)

        # 分页
        total = len(elements)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_elements = elements[start_idx:end_idx]

        return {"success": True, "data": paged_elements, "total": total}

    except Exception as e:
        logger.exception(f"获取元素列表时出错: {e}")
        return {"success": False, "message": f"获取元素列表失败: {str(e)}", "data": [], "total": 0}
