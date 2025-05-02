"""
任务会话服务模块

提供任务与工作流会话的关联管理功能。
"""

import logging
from typing import Any, Dict, List, Optional

from src.db.repositories.task_repository import TaskRepository
from src.db.session_manager import session_scope

logger = logging.getLogger(__name__)


class TaskSessionService:
    """任务会话服务类，负责任务与工作流会话的关联管理"""

    def __init__(self, status_service):
        """初始化任务会话服务

        Args:
            status_service: 状态服务实例
        """
        self._task_repo = TaskRepository()
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

                # 使用 session_scope 获取数据库会话获取任务详情并更新项目状态
                with session_scope() as db_session:
                    # 获取任务详情
                    task = self._task_repo.get_by_id(db_session, task_id)
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
            # 使用 session_scope 获取数据库会话
            with session_scope() as db_session:
                # 添加任务验证
                task = self._task_repo.get_by_id(db_session, task_id)
                if not task:
                    error_msg = f"无法关联工作流会话，因为找不到任务 (ID: {task_id})"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                else:
                    logger.debug(f"验证通过：找到任务 {task_id} (标题: {task.title})，可以继续关联会话")

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
                    session_obj = session_manager.get_session(session_id)
                    if session_obj:
                        # 更新会话关联到任务
                        updated_session = session_manager.update_session(session_obj.id, {"task_id": task_id})
                        if updated_session:
                            session = updated_session
                            # 设置为当前会话
                            session_manager.switch_session(session.id)
                        else:
                            error_msg = f"更新会话 '{session_id}' 失败"
                            logger.error(error_msg)
                            raise ValueError(error_msg)
                    else:
                        error_msg = f"找不到会话 '{session_id}'，请确认会话ID是否正确"
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                else:
                    # 如果既没有 flow_type 也没有 session_id
                    error_msg = "必须提供 flow_type (创建新会话) 或 session_id (关联现有会话)"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                if session:
                    # 更新任务的当前会话
                    updated_task = self._task_repo.update_task(db_session, task_id, {"current_session_id": session.id})
                    if not updated_task:
                        error_msg = f"更新任务 {task_id} 的 current_session_id 失败"
                        logger.error(error_msg)
                        # Consider rolling back or raising a different error
                        raise ValueError(error_msg)
                    # 设置当前任务
                    self.set_current_task(task_id)
                    return session.to_dict()
                else:
                    # 这段逻辑理论上不应该被执行，因为前面已经处理了失败情况
                    error_msg = "未能创建或关联工作流会话"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
        except ValueError as e:
            # 传递验证错误
            raise e
        except Exception as e:
            error_msg = f"关联任务到工作流会话失败: {e}"
            logger.error(error_msg, exc_info=True)  # 添加 exc_info
            raise ValueError(error_msg)

    def link_to_workflow(self, task_id: str, workflow_id: str) -> Optional[Dict[str, Any]]:
        """直接关联任务到工作流定义（不创建会话）

        Args:
            task_id: 任务ID
            workflow_id: 工作流ID或名称

        Returns:
            关联的工作流信息，失败返回None

        Raises:
            ValueError: 当找不到指定的工作流或任务时
        """
        try:
            logger.info(f"开始将任务 {task_id} 关联到工作流 {workflow_id}")

            # 使用 session_scope 获取数据库会话
            with session_scope() as db_session:
                # 验证任务存在
                task = self._task_repo.get_by_id(db_session, task_id)
                if not task:
                    error_msg = f"无法关联工作流，因为找不到任务 (ID: {task_id})"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                # 使用工作流搜索工具查找工作流
                from src.workflow.utils.workflow_search import get_workflow_fuzzy

                workflow = get_workflow_fuzzy(workflow_id)
                if not workflow:
                    error_msg = f"找不到工作流 '{workflow_id}'，请确认ID或名称是否正确"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                real_workflow_id = workflow["id"]
                workflow_name = workflow.get("name", "未命名工作流")
                logger.info(f"已找到工作流: {workflow_name} (ID: {real_workflow_id})")

                # 更新任务的工作流关联
                try:
                    updated_task = self._task_repo.update_task(
                        db_session,
                        task_id,
                        {
                            "workflow_id": real_workflow_id,
                            # 可以添加其他需要更新的工作流相关字段
                        },
                    )

                    if not updated_task:
                        error_msg = f"更新任务 {task_id} 的工作流关联失败"
                        logger.error(error_msg)
                        raise ValueError(error_msg)

                    # 自动创建工作流执行指南 (session)，但对用户透明
                    try:
                        logger.info(f"正在为任务 {task_id} 创建工作流执行指南...")

                        # 创建FlowSessionManager实例
                        from src.flow_session.manager import FlowSessionManager

                        session_manager = FlowSessionManager(db_session)

                        # 获取任务详情用于创建更有意义的会话
                        task_details = self._task_repo.get_by_id(db_session, task_id)
                        task_title = task_details.title if task_details else f"Task-{task_id[:8]}"

                        # 创建工作流会话
                        session_name = f"{workflow_name}-{task_title[:20]}"
                        session = session_manager.create_session(
                            workflow_id=real_workflow_id, name=session_name, task_id=task_id, flow_type=workflow.get("type")
                        )

                        # 更新任务的当前会话
                        if session:
                            self._task_repo.update_task(db_session, task_id, {"current_session_id": session.id})
                            logger.info(f"成功创建工作流执行指南: {session.id}")

                            # 生成执行指南内容 (这里可以调用 LLM 生成更详细的指南)
                            try:
                                # 异步触发执行指南生成，不阻塞主流程
                                import threading

                                from src.flow_session.core.session_context import generate_context_for_session

                                def generate_context_thread():
                                    try:
                                        with session_scope() as inner_session:
                                            generate_context_for_session(inner_session, session.id)
                                    except Exception as e:
                                        logger.error(f"生成执行指南内容失败: {e}", exc_info=True)

                                # 启动线程异步生成
                                threading.Thread(target=generate_context_thread).start()
                                logger.info(f"已触发执行指南内容生成")
                            except Exception as e:
                                logger.warning(f"触发执行指南内容生成失败: {e}")
                    except Exception as e:
                        # 这里不要抛出异常，因为工作流关联已成功，执行指南创建是附加功能
                        logger.warning(f"创建工作流执行指南失败: {e}", exc_info=True)

                    # 设置为当前任务
                    self.set_current_task(task_id)

                    # 返回工作流信息
                    return {
                        "id": real_workflow_id,
                        "name": workflow_name,
                        "type": workflow.get("type", "未知类型"),
                        # 可以添加其他需要返回的工作流信息
                    }
                except Exception as e:
                    error_msg = f"关联任务到工作流失败: {str(e)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

        except ValueError as e:
            # 传递验证错误
            raise e
        except Exception as e:
            error_msg = f"关联任务到工作流失败: {e}"
            logger.error(error_msg, exc_info=True)
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
            # 使用 session_scope 获取数据库会话
            with session_scope() as db_session:
                # 获取所有关联会话
                from src.db.repositories.flow_session_repository import FlowSessionRepository

                # 直接实例化 FlowSessionRepository
                flow_repo = FlowSessionRepository()
                sessions = flow_repo.get_by_task_id(db_session, task_id)

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
            with session_scope() as db_session:
                task = self._task_repo.get_by_id(db_session, current_task_id)

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

                # FlowSessionManager 需要会话，在 with 块内创建
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

            # 使用 session_scope 获取数据库会话
            with session_scope() as db_session:
                # 验证会话是否存在
                from src.flow_session.manager import FlowSessionManager

                # FlowSessionManager 需要会话，在 with 块内创建
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
                # task = self._task_repo.get_by_id(db_session, current_task_id)
                # if not task:
                #     logger.error(f"设置当前工作流会话失败: 任务 {current_task_id} 不存在")
                #     return False
                # task.current_session_id = session_id
                # self._task_repo.update(db_session, task) # 基类没有update(session, obj)

                # 使用 update_task 方法
                updated_task = self._task_repo.update_task(db_session, current_task_id, {"current_session_id": session_id})
                if not updated_task:
                    logger.error(f"更新任务 {current_task_id} 的 current_session_id 失败")
                    return False

                # db_session.commit() # session_scope 会自动处理 commit/rollback

                # 使用 Provider 设置当前会话
                session_provider = self._status_service.provider_manager.get_provider("flow_session")
                if session_provider and hasattr(session_provider, "set_current_session"):
                    session_provider.set_current_session(session_id)

                # 更新任务状态
                # 获取更新后的任务状态以传递
                task_status_val = updated_task.status if updated_task else "unknown"
                self._status_service.update_status(domain="task", entity_id=current_task_id, status=task_status_val, current_session_id=session_id)

                # 同时更新工作流状态
                self._status_service.update_status(domain="workflow", entity_id=f"flow-{session_id}", status="IN_PROGRESS")

                return True

        except Exception as e:
            logger.error(f"设置当前工作流会话失败: {e}")
            return False
