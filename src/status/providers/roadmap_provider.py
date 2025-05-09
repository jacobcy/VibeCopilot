"""
路线图状态提供者模块

实现路线图的状态提供者接口，适配 RoadmapStatus。
"""

import json  # 需要 json 模块
import logging
import os  # 需要 os 模块
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# 导入 get_config
from src.core.config import get_config
from src.db.session_manager import session_scope  # 需要 session_scope
from src.status.core.project_state import ProjectState  # 导入 ProjectState

# 移除 RoadmapService 的直接导入
# from src.roadmap.service.roadmap_service import RoadmapService
# --- 移除对已删除的 RoadmapStatus 的导入 ---
# from src.roadmap.service.roadmap_status import RoadmapStatus
# ------------------------------------------
from src.status.interfaces import IStatusProvider

# 处理循环导入的类型提示
if TYPE_CHECKING:
    from src.roadmap.service.roadmap_service import RoadmapService

logger = logging.getLogger(__name__)


class RoadmapStatusProvider(IStatusProvider):
    """路线图状态提供者

    现在也负责管理活动路线图ID的持久化状态。
    """

    def __init__(self, project_state: ProjectState):  # 接收 ProjectState 实例
        """初始化路线图状态提供者 (不再接收 roadmap_service)

        Args:
            project_state: ProjectState 实例
        """
        # 初始化服务和检查器为 None，等待 set_service 调用
        self.roadmap_service: Optional["RoadmapService"] = None
        self.project_state = project_state  # 存储 ProjectState 实例
        logger.info("RoadmapStatusProvider 已初始化，使用 ProjectState 管理活动路线图ID")

    def _get_project_state(self):
        """获取ProjectState实例"""
        from src.status.service import StatusService

        return StatusService.get_instance().project_state

    def set_service(self, roadmap_service: "RoadmapService"):
        """注入 RoadmapService 实例并完成初始化。"""
        if self.roadmap_service:
            logger.info("RoadmapService 已被设置，将被覆盖。")
        self.roadmap_service = roadmap_service
        logger.info("RoadmapStatusProvider 已成功注入 RoadmapService。")
        # 可以在这里触发一次加载时验证（如果需要）
        self._validate_loaded_active_id()

    def _ensure_service_set(self):
        """确保RoadmapService已设置

        Raises:
            RuntimeError: 如果RoadmapService未设置
        """
        if not self.roadmap_service:  # Check the instance variable directly
            logger.warning("RoadmapStatusProvider: self.roadmap_service is None. Attempting to fetch from connector.")
            try:
                from src.roadmap.service.service_connector import connect_services, get_roadmap_service

                # Try to get an existing service instance from the connector first
                rs_instance = get_roadmap_service()
                if rs_instance:
                    self.set_service(rs_instance)  # This will set self.roadmap_service
                    logger.info("RoadmapStatusProvider: Successfully fetched and set RoadmapService from connector.")
                else:
                    # If not found, it might mean RoadmapService hasn't been instantiated and registered yet.
                    # Calling connect_services() might trigger its registration if it's a timing issue.
                    logger.warning("RoadmapStatusProvider: RoadmapService not found in connector. Triggering connect_services().")
                    connect_services()  # This might lead to set_service being called on this provider
                    if not self.roadmap_service:  # Check again if connect_services set it
                        logger.error("RoadmapStatusProvider: RoadmapService still not set after attempting to fetch and connect.")
                        raise RuntimeError("RoadmapService 尚未在 RoadmapStatusProvider 上设置（连接尝试后）。")
            except ImportError:
                logger.error("RoadmapStatusProvider: 无法导入 service_connector 模块。")
                raise RuntimeError("RoadmapService 连接模块导入失败。")
            except Exception as e:
                logger.error(f"RoadmapStatusProvider: _ensure_service_set 中发生错误: {e}", exc_info=True)
                raise RuntimeError(f"RoadmapService 设置时出错: {e}")

        # If self.roadmap_service was set by the above logic, or was already set.
        if not self.roadmap_service:
            # This is a fallback, should ideally not be reached if above logic is correct
            logger.critical("RoadmapStatusProvider: _ensure_service_set Fallback - RoadmapService is still None.")
            raise RuntimeError("RoadmapService 尚未在 RoadmapStatusProvider 上设置（最终检查）。")

    def _validate_loaded_active_id(self):
        """验证内存中的活动ID是否有效，通常在 set_service 后调用。"""
        self._ensure_service_set()
        # 从 ProjectState 获取当前路线图ID
        loaded_id = self.project_state.get_current_roadmap_id()
        if not loaded_id:
            logger.info("当前未设置活动路线图ID，跳过验证。")
            return

        # 使用更完善的验证方法检查路线图是否存在
        try:
            with session_scope() as session:
                # 尝试直接从数据库获取路线图
                roadmap = self.roadmap_service.roadmap_repo.get_by_id(session, loaded_id)
                if roadmap:
                    logger.info(f"先前加载的活动路线图ID {loaded_id} 验证通过，标题: {roadmap.title}。")
                    return

                # 如果直接查询未找到，尝试使用roadmap服务的更高级方法
                roadmap_data = self.roadmap_service.get_roadmap(loaded_id)
                if roadmap_data:
                    logger.info(f"先前加载的活动路线图ID {loaded_id} 通过服务验证通过，标题: {roadmap_data.get('title', '未知')}。")
                    return
        except Exception as e:
            logger.error(f"验证路线图ID {loaded_id} 时出错: {e}", exc_info=True)

            # 如果所有验证方法都失败，才清除路线图ID
            logger.warning(f"先前加载的活动路线图ID {loaded_id} 无效，将清除。")
            self.project_state.set_current_roadmap_id(None)

    def _validate_roadmap_exists(self, roadmap_id: str) -> bool:
        """验证给定的 roadmap_id 是否在数据库中存在"""
        self._ensure_service_set()  # 确保服务已设置
        if not roadmap_id:
            return False
        try:
            with session_scope() as session:
                # 使用注入的 RoadmapService 里的 repo
                roadmap = self.roadmap_service.roadmap_repo.get_by_id(session, roadmap_id)
                return roadmap is not None
        except Exception as e:
            logger.error(f"验证路线图ID {roadmap_id} 存在性时出错: {e}", exc_info=True)
            return False  # 无法验证时视为不存在

    def set_active_roadmap_id(self, roadmap_id: str) -> bool:
        """设置当前活跃路线图ID

        Args:
            roadmap_id: 路线图ID

        Returns:
            bool: 操作是否成功
        """
        try:
            # 仅更新ProjectState中的当前路线图ID
            self.project_state.set_current_roadmap_id(roadmap_id)
            logger.info(f"已将活跃路线图ID设置为: {roadmap_id}（通过ProjectState）")
            return True
        except Exception as e:
            logger.error(f"设置活跃路线图ID时出错: {str(e)}")
            return False

    def get_active_roadmap_id(self) -> Optional[str]:
        """获取当前活跃路线图ID

        Returns:
            Optional[str]: 当前活跃路线图ID，如果没有则返回None
        """
        try:
            # 仅从ProjectState获取
            roadmap_id = self.project_state.get_current_roadmap_id()
            if not roadmap_id:
                # 如果没有活动路线图ID，返回None而不是空字符串
                return None
            return roadmap_id
        except Exception as e:
            logger.error(f"获取活跃路线图ID时出错: {str(e)}")
            return None

    # --- 现有方法保持不变，但使用 self.roadmap_status_checker ---

    @property
    def domain(self) -> str:
        """获取状态提供者的领域名称"""
        return "roadmap"

    def get_status(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"RoadmapStatusProvider.get_status called with entity_id: {entity_id}")  # DEBUG LINE
        self._ensure_service_set()
        try:
            check_type = "roadmap"
            element_id_to_check = None

            if entity_id:
                if ":" in entity_id:
                    entity_type, real_id = entity_id.split(":", 1)
                    check_type = entity_type  # 可能是 "roadmap", "epic", "story", "task"
                    element_id_to_check = real_id
                else:
                    # 如果没有冒号，假设是直接的ID
                    element_id_to_check = entity_id

            # 获取当前活动的路线图ID
            active_roadmap_id = self.get_active_roadmap_id()

            # 确定要检查的路线图ID - 如果指定了特定roadmap
            roadmap_id_to_check = None
            if check_type == "roadmap" and element_id_to_check:
                roadmap_id_to_check = element_id_to_check
            else:
                roadmap_id_to_check = active_roadmap_id

            # 准备返回数据
            status_data = {
                "active_roadmap_id": active_roadmap_id,
                "status": "unknown",
                "health": "unknown",
                "roadmap_id": roadmap_id_to_check,
                "check_type": check_type,
                "element_id": element_id_to_check,
                "error": None,
                "entity_data": None,
                "children": None,
                "full_path": None,
            }
            logger.info(f"Initial status_data: {status_data}")  # DEBUG LINE

            # 如果没有路线图ID可检查，直接返回
            if not roadmap_id_to_check:
                status_data["status"] = "no_active_roadmap"
                status_data["error"] = "没有活动路线图或未指定要检查的路线图ID。"
                logger.info(f"Returning due to no roadmap_id_to_check. status_data: {status_data}")  # DEBUG LINE
                return status_data

            # 收集实体数据
            with session_scope() as session:
                try:
                    # 根据检查类型和ID查询实体数据
                    if check_type == "roadmap":
                        roadmap = self.roadmap_service.roadmap_repo.get_by_id(session, roadmap_id_to_check)
                        if roadmap:
                            status_data["entity_data"] = {
                                "id": roadmap.id,
                                "title": roadmap.title,
                                "description": roadmap.description,
                                "status": roadmap.status,
                                "created_at": roadmap.created_at if roadmap.created_at else None,
                                "updated_at": roadmap.updated_at if roadmap.updated_at else None,
                            }

                            # 获取史诗列表
                            epics = self.roadmap_service.epic_repo.get_by_roadmap_id(session, roadmap.id)
                            if epics:
                                children = []
                                for epic in epics:
                                    children.append({"id": epic.id, "title": epic.title, "status": epic.status})
                                status_data["children"] = children

                            status_data["status"] = roadmap.status
                            status_data["health"] = "good"  # Could be calculated
                            if not roadmap:
                                status_data["status"] = "not_found"
                                status_data["error"] = f"找不到路线图 ID: {roadmap_id_to_check}"
                                logger.info(f"Roadmap not found. status_data: {status_data}")  # DEBUG LINE
                        else:
                            status_data["status"] = "not_found"
                            status_data["error"] = f"找不到路线图 ID: {roadmap_id_to_check}"
                            logger.info(f"Roadmap not found. status_data: {status_data}")  # DEBUG LINE

                    elif check_type == "epic":
                        # 查询史诗数据
                        if not element_id_to_check:
                            status_data["error"] = "没有提供史诗ID"
                            logger.info(f"No epic_id provided. status_data: {status_data}")  # DEBUG LINE
                            return status_data

                        epic = self.roadmap_service.epic_repo.get_by_id(session, element_id_to_check)
                        if epic:
                            status_data["entity_data"] = {
                                "id": epic.id,
                                "title": epic.title,
                                "description": epic.description,
                                "status": epic.status,
                                "created_at": epic.created_at.isoformat() if epic.created_at else None,
                                "roadmap_id": epic.roadmap_id,
                            }

                            # 获取故事列表
                            stories = self.roadmap_service.story_repo.get_by_epic_id(session, epic.id)
                            if stories:
                                children = []
                                for story in stories:
                                    children.append({"id": story.id, "title": story.title, "status": story.status})
                                status_data["children"] = children

                            # 设置完整路径
                            roadmap = self.roadmap_service.roadmap_repo.get_by_id(session, epic.roadmap_id)
                            if roadmap:
                                status_data["full_path"] = f"{roadmap.title} > {epic.title}"

                            status_data["status"] = epic.status
                            status_data["health"] = "good"  # Could be calculated
                            if not epic:
                                status_data["status"] = "not_found"
                                status_data["error"] = f"找不到史诗 ID: {element_id_to_check}"
                                logger.info(f"Epic not found. status_data: {status_data}")  # DEBUG LINE
                        else:
                            status_data["status"] = "not_found"
                            status_data["error"] = f"找不到史诗 ID: {element_id_to_check}"
                            logger.info(f"Epic not found. status_data: {status_data}")  # DEBUG LINE

                    # 可以类似地添加 "story" 和 "task" 的处理
                    else:
                        # 如果 check_type 未知或未处理
                        if not status_data.get("error"):
                            status_data["error"] = f"不支持的检查类型 '{check_type}' 或未能获取详细信息。"
                            status_data["status"] = "unknown_type_or_incomplete_data"
                            logger.info(f"Unknown check_type. status_data: {status_data}")  # DEBUG LINE

                except Exception as e_inner:
                    error_msg_inner = str(e_inner) if str(e_inner) else repr(e_inner)
                    status_data["error"] = f"查询数据时出错: {error_msg_inner}"
                    logger.error(f"查询路线图状态数据时出错: {e_inner}", exc_info=True)
                    logger.info(f"Error in session_scope. status_data: {status_data}")  # DEBUG LINE

            logger.info(f"Before final return from try block. status_data: {status_data}")  # DEBUG LINE
            return status_data

        except Exception as e_outer:
            logger.error(f"获取路线图状态时外层出错: {e_outer}", exc_info=True)
            error_message = str(e_outer) if str(e_outer) else repr(e_outer)
            if not error_message or error_message == "None":  # Defensive check
                error_message = "获取路线图状态时发生未知内部错误。请检查日志。"

            # Ensure status_data is initialized if e_outer happened very early
            if "status_data" not in locals():
                status_data = {"error": "Initialization error before status_data creation"}

            status_data["error"] = error_message
            if "active_roadmap_id" not in status_data:  # Ensure active_roadmap_id is present for debugging
                current_active_id = None
                try:
                    current_active_id = self.get_active_roadmap_id()
                except Exception:
                    pass  # Ignore if get_active_roadmap_id itself fails
                status_data["active_roadmap_id"] = current_active_id

            logger.info(f"Error in outer except block. status_data: {status_data}")  # DEBUG LINE
            return status_data

    def update_status(self, entity_id: str, status: str, **kwargs) -> Dict[str, Any]:
        """更新路线图相关实体的状态

        Args:
            entity_id: 实体ID，格式为 'type:id'
            status: 新状态值
            **kwargs: 额外的更新参数

        Returns:
            包含更新结果的字典
        """
        self._ensure_service_set()
        try:
            if ":" not in entity_id:
                return {"updated": False, "error": "无效的实体ID格式，应为 'type:id'"}

            entity_type, entity_id = entity_id.split(":", 1)

            with session_scope() as session:
                # 根据实体类型和ID更新状态
                if entity_type == "roadmap":
                    roadmap = self.roadmap_service.roadmap_repo.get_by_id(session, entity_id)
                    if roadmap:
                        roadmap.status = status
                        session.commit()
                        return {"updated": True, "entity_type": entity_type, "entity_id": entity_id, "new_status": status}
                    else:
                        return {"updated": False, "error": f"找不到路线图 ID: {entity_id}"}

                elif entity_type == "epic":
                    epic = self.roadmap_service.epic_repo.get_by_id(session, entity_id)
                    if epic:
                        epic.status = status
                        session.commit()
                        return {"updated": True, "entity_type": entity_type, "entity_id": entity_id, "new_status": status}
                    else:
                        return {"updated": False, "error": f"找不到史诗 ID: {entity_id}"}

                # 可以类似地添加 "story" 和 "task" 的状态更新处理

                return {"updated": False, "error": f"不支持的实体类型: {entity_type}"}

        except Exception as e:
            logger.error(f"更新路线图状态时出错: {e}", exc_info=True)
            return {"updated": False, "error": f"更新路线图状态时出错: {e}"}

    def list_entities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出路线图相关实体

        Args:
            status: 可选的状态过滤器

        Returns:
            实体列表
        """
        self._ensure_service_set()
        entities = []

        try:
            with session_scope() as session:
                # 获取路线图列表
                roadmaps = self.roadmap_service.roadmap_repo.get_all(session)
                active_roadmap_id = self.get_active_roadmap_id()

                for roadmap in roadmaps:
                    # 如果指定了状态过滤，且不匹配则跳过
                    if status and roadmap.status != status:
                        continue

                    entity = {
                        "id": f"roadmap:{roadmap.id}",
                        "title": roadmap.title,
                        "status": roadmap.status,
                        "type": "roadmap",
                        "active": roadmap.id == active_roadmap_id,
                    }
                    entities.append(entity)

            return entities

        except Exception as e:
            logger.error(f"列出路线图实体时出错: {e}", exc_info=True)
            return []
