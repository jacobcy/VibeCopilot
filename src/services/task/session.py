"""
任务会话服务模块

提供任务与工作流会话的关联管理功能。
"""

import logging
from typing import Any, Dict, List, Optional

from loguru import logger

from src.db import get_session_factory

logger = logging.getLogger(__name__)


class TaskSessionService:
    """任务会话服务类，负责任务与工作流会话的关联管理"""

    def __init__(self, db_service, status_service):
        """初始化任务会话服务

        Args:
            db_service: 数据库服务实例
            status_service: 状态服务实例
        """
        self._db_service = db_service
        self._status_service = status_service

    def set_current_task(self, task_id: str) -> bool:
        """设置当前任务

        设置指定任务为当前任务，同时如果任务有关联的会话，将该会话设置为当前会话。
        现在使用 Provider 模式，不再直接操作数据库的 is_current 字段。

        Args:
            task_id: 任务ID

        Returns:
            是否设置成功
        """
        try:
            # 使用 Provider 设置当前任务
            task_provider = self._status_service.provider_manager.get_provider("task")

            if task_provider and hasattr(task_provider, "set_current_task"):
                # 设置当前任务
                task_provider.set_current_task(task_id)

                # 使用会话工厂获取数据库会话获取任务详情并更新项目状态
                with get_session_factory()() as db_session:
                    # 获取任务详情
                    task = self._db_service.task_repo.get_by_id(db_session, task_id)
                    if task:
                        # 通过状态服务更新当前任务
                        self._status_service.update_project_state("current_task", {"id": task_id, "title": task.title, "status": task.status})

                        # 如果任务有关联的会话，也将该会话设置为当前会话
                        if task.current_session_id:
                            try:
                                # 使用 Provider 设置当前会话
                                session_provider = self._status_service.provider_manager.get_provider("flow_session")
                                if session_provider and hasattr(session_provider, "set_current_session"):
                                    session_provider.set_current_session(task.current_session_id)

                                    # 通过状态服务更新当前工作流会话
                                    self._status_service.update_status(
                                        domain="workflow", entity_id=f"flow-{task.current_session_id}", status="IN_PROGRESS"
                                    )
                            except Exception as e:
                                logger.error(f"设置关联会话为当前会话失败: {e}")

                return True
            else:
                logger.error("找不到 TaskStatusProvider 或 set_current_task 方法")
                return False

        except Exception as e:
            logger.error(f"设置当前任务失败: {e}", exc_info=True)  # Log traceback
            return False

    def link_to_flow_session(self, task_id: str, flow_type: str = None, session_id: str = None) -> Optional[Dict[str, Any]]:
        """关联任务到工作流会话

        Args:
            task_id: 任务ID
            flow_type: 工作流ID或名称，用于创建新会话
            session_id: 现有会话ID，用于关联到已有会话

        Returns:
            关联的会话信息，失败返回None

        Raises:
            ValueError: 当找不到指定的工作流或会话时
        """
        try:
            # 获取数据库会话
            from src.db import get_session_factory

            session_factory = get_session_factory()
            with session_factory() as db_session:
                # 创建FlowSessionManager实例
                from src.flow_session.manager import FlowSessionManager

                session_manager = FlowSessionManager(db_session)

                if flow_type:
                    # 使用工作流搜索工具查找工作流
                    from src.workflow.utils.workflow_search import get_workflow_fuzzy

                    workflow = get_workflow_fuzzy(flow_type)
                    if not workflow:
                        error_msg = f"找不到工作流 '{flow_type}'，请确认ID或名称是否正确"
                        logger.error(error_msg)
                        raise ValueError(error_msg)

                    workflow_id = workflow["id"]
                    workflow_name = workflow.get("name", "未命名工作流")
                    logger.info(f"已找到工作流: {workflow_name} (ID: {workflow_id})")

                    # 创建新会话
                    try:
                        new_session = session_manager.create_session(
                            workflow_id=workflow_id, name=f"{workflow_name}-{task_id[:8]}", task_id=task_id, flow_type=workflow.get("type")
                        )
                        session = new_session
                    except ValueError as e:
                        error_msg = f"创建工作流会话失败: {str(e)}"
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                elif session_id:
                    # 关联到已有会话
                    session = session_manager.get_session(session_id)
                    if session:
                        # 更新会话关联到任务
                        session_manager.update_session(session.id, {"task_id": task_id})
                        # 设置为当前会话
                        session_manager.switch_session(session.id)
                    else:
                        error_msg = f"找不到会话 '{session_id}'，请确认会话ID是否正确"
                        logger.error(error_msg)
                        raise ValueError(error_msg)

                if session:
                    # 更新任务的当前会话
                    self._db_service.task_repo.update_task(task_id, {"current_session_id": session.id})
                    # 设置当前任务
                    self.set_current_task(task_id)
                    return session.to_dict()
                else:
                    error_msg = "未能创建或关联工作流会话"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
        except ValueError as e:
            # 传递验证错误
            raise e
        except Exception as e:
            error_msg = f"关联任务到工作流会话失败: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def create_task_with_flow(self, task_service, task_data: Dict[str, Any], workflow_id: str) -> Optional[Dict[str, Any]]:
        """创建任务并自动关联工作流会话

        Args:
            task_service: 任务服务实例
            task_data: 任务数据
            workflow_id: 工作流定义ID或名称

        Returns:
            创建的任务数据，包含关联的工作流会话信息

        Raises:
            ValueError: 当任务创建或工作流关联失败时
        """
        try:
            logger.info(f"开始创建任务并关联工作流: {workflow_id}")

            # 1. 创建任务
            task = task_service.create_task(task_data)
            if not task:
                error_msg = "创建任务失败，请检查任务数据是否有效"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(f"成功创建任务: {task['title']} (ID: {task['id']})")

            # 2. 使用工作流搜索工具查找工作流
            from src.workflow.utils.workflow_search import get_workflow_fuzzy

            try:
                workflow = get_workflow_fuzzy(workflow_id)
                if not workflow:
                    # 获取所有可用工作流，提供更好的错误信息
                    from src.workflow.service import list_workflows

                    all_workflows = list_workflows()
                    workflow_names = [wf.get("name", "未命名") for wf in all_workflows]
                    workflow_ids = [wf.get("id", "") for wf in all_workflows]

                    error_msg = f"找不到ID或名称为 '{workflow_id}' 的工作流"
                    if workflow_names:
                        error_msg += f"，可用的工作流有: {', '.join(workflow_names)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            except Exception as e:
                error_msg = f"查找工作流失败: {str(e)}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            real_workflow_id = workflow["id"]
            logger.info(f"找到工作流: {workflow.get('name', '未命名工作流')} (ID: {real_workflow_id})")

            # 3. 创建工作流会话
            try:
                from src.flow_session.core.session_create import handle_create_session

                session_result = handle_create_session(
                    workflow_id=real_workflow_id, name=f"Flow for {task['title']}", task_id=task["id"], verbose=False, agent_mode=True
                )

                if not session_result["success"]:
                    error_msg = session_result.get("error_message", "创建工作流会话失败，但未提供详细原因")
                    logger.error(f"创建工作流会话失败: {error_msg}")
                    raise ValueError(f"创建工作流会话失败: {error_msg}")
            except Exception as e:
                error_msg = f"创建工作流会话过程中出错: {str(e)}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(f"成功创建工作流会话: {session_result['session'].get('id')}")

            # 4. 更新任务数据，添加会话信息
            task["flow_session"] = session_result["session"]

            # 5. 通过状态服务更新状态
            # 更新任务状态
            self._status_service.update_status(
                domain="task", entity_id=task["id"], status=task.get("status", "created"), current_session_id=session_result["session"]["id"]
            )

            # 更新工作流状态
            self._status_service.update_status(domain="workflow", entity_id=f"flow-{session_result['session']['id']}", status="IN_PROGRESS")

            # 更新项目状态中的当前任务
            self._status_service.update_project_state(
                "current_task",
                {
                    "id": task["id"],
                    "title": task["title"],
                    "status": task.get("status", "created"),
                    "current_session_id": session_result["session"]["id"],
                },
            )

            return task
        except ValueError as e:
            # 传递验证错误
            raise e
        except Exception as e:
            error_msg = f"创建任务并关联工作流失败: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def get_task_sessions(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务关联的所有工作流会话

        Args:
            task_id: 任务ID

        Returns:
            工作流会话列表
        """
        try:
            # 获取数据库会话
            from src.db import get_session_factory

            # 使用with语句确保会话自动关闭
            with get_session_factory()() as db_session:
                # 获取所有关联会话
                from src.db.repositories.flow_session_repository import FlowSessionRepository

                flow_repo = FlowSessionRepository(db_session)
                sessions = flow_repo.get_by_task_id(task_id)

                # 转换为字典格式并返回
                return [session.to_dict() for session in sessions]

        except Exception as e:
            logger.error(f"获取任务工作流会话失败: {e}")
            return []

    def get_current_task_session(self) -> Optional[Dict[str, Any]]:
        """获取当前任务的当前工作流会话

        现在使用 Provider 模式获取当前任务 ID。

        Returns:
            当前工作流会话信息，如果不存在则返回None
        """
        try:
            # 首先使用 Provider 获取当前任务 ID
            task_provider = self._status_service.provider_manager.get_provider("task")
            current_task_id = None

            if task_provider and hasattr(task_provider, "get_current_task_id"):
                # 使用 Provider 获取当前任务 ID
                current_task_id = task_provider.get_current_task_id()

            # 如果使用 Provider 获取失败，尝试从状态服务获取当前任务信息
            if not current_task_id:
                task_status = self._status_service.get_domain_status("task")
                current_task = task_status.get("current_task")

                if current_task:
                    current_task_id = current_task.get("id")

            # 如果还是没有找到当前任务 ID，返回 None
            if not current_task_id:
                return None

            # 获取任务详情
            with get_session_factory()() as db_session:
                task = self._db_service.task_repo.get_by_id(db_session, current_task_id)

                if not task:
                    return None

                # 获取任务的 current_session_id
                session_id = task.current_session_id
                if not session_id:
                    return None

                # 尝试从状态服务获取工作流会话
                workflow_status = self._status_service.get_domain_status("workflow", f"flow-{session_id}")
                if workflow_status and "error" not in workflow_status:
                    return workflow_status

                # 获取会话详情
                from src.flow_session.manager import FlowSessionManager

                session_manager = FlowSessionManager(db_session)

                # 获取会话
                session = session_manager.get_session(session_id)
                return session.to_dict() if session else None

        except Exception as e:
            logger.error(f"获取当前任务工作流会话失败: {e}")
            return None

    def set_current_task_session(self, session_id: str) -> bool:
        """设置当前任务的当前工作流会话

        现在使用 Provider 模式设置当前会话和获取当前任务。

        Args:
            session_id: 会话ID

        Returns:
            操作是否成功
        """
        try:
            # 获取当前任务
            current_task_id = None

            # 首先使用 Provider 获取当前任务 ID
            task_provider = self._status_service.provider_manager.get_provider("task")
            if task_provider and hasattr(task_provider, "get_current_task_id"):
                current_task_id = task_provider.get_current_task_id()

            # 如果使用 Provider 获取失败，尝试从状态服务获取当前任务信息
            if not current_task_id:
                task_status = self._status_service.get_domain_status("task")
                current_task = task_status.get("current_task")

                if current_task:
                    current_task_id = current_task.get("id")

            # 如果还是没有找到当前任务 ID，返回失败
            if not current_task_id:
                logger.error("设置当前工作流会话失败: 当前没有活动任务")
                return False

            # 获取数据库会话
            with get_session_factory()() as db_session:
                # 验证会话是否存在
                from src.flow_session.manager import FlowSessionManager

                session_manager = FlowSessionManager(db_session)

                # 获取会话
                session = session_manager.get_session(session_id)

                if not session:
                    logger.error(f"设置当前工作流会话失败: 会话 {session_id} 不存在")
                    return False

                # 验证会话是否属于当前任务
                if session.task_id != current_task_id:
                    logger.error(f"设置当前工作流会话失败: 会话 {session_id} 不属于当前任务 {current_task_id}")
                    return False

                # 更新任务的 current_session_id
                task = self._db_service.task_repo.get_by_id(db_session, current_task_id)
                if not task:
                    logger.error(f"设置当前工作流会话失败: 任务 {current_task_id} 不存在")
                    return False

                task.current_session_id = session_id
                self._db_service.task_repo.update(db_session, task)
                db_session.commit()

                # 使用 Provider 设置当前会话
                session_provider = self._status_service.provider_manager.get_provider("flow_session")
                if session_provider and hasattr(session_provider, "set_current_session"):
                    session_provider.set_current_session(session_id)

                # 更新任务状态
                self._status_service.update_status(domain="task", entity_id=current_task_id, status=task.status, current_session_id=session_id)

                # 同时更新工作流状态
                self._status_service.update_status(domain="workflow", entity_id=f"flow-{session_id}", status="IN_PROGRESS")

                return True

        except Exception as e:
            logger.error(f"设置当前工作流会话失败: {e}")
            return False
