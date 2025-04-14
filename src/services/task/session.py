"""
任务会话服务模块

提供任务与工作流会话的关联管理功能。
"""

import logging
from typing import Any, Dict, List, Optional

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

        Args:
            task_id: 任务ID

        Returns:
            是否设置成功
        """
        try:
            success = self._db_service.task_repo.set_current_task(task_id)

            # 获取任务的关联会话ID，并确保其为当前会话
            if success:
                # 获取更新后的任务
                task = self._db_service.task_repo.get_by_id(task_id)
                if task:
                    # 通过状态服务更新当前任务
                    self._status_service.update_project_state("current_task", {"id": task_id, "title": task.title, "status": task.status})

                    if task.current_session_id:
                        # 使用已有的会话管理器确保会话是当前会话
                        try:
                            # 获取会话
                            from src.db import get_session_factory

                            db_session = get_session_factory()()  # 创建新的会话

                            from src.flow_session.manager import FlowSessionManager

                            session_manager = FlowSessionManager(db_session)
                            try:
                                session_manager.switch_session(task.current_session_id)

                                # 通过状态服务更新当前工作流会话
                                self._status_service.update_status(
                                    domain="workflow", entity_id=f"flow-{task.current_session_id}", status="IN_PROGRESS"
                                )
                            except Exception as e:
                                logger.error(f"切换到关联会话失败: {e}")
                            finally:
                                db_session.close()  # 确保关闭会话
                        except Exception as e:
                            logger.error(f"获取数据库会话失败: {e}")

            return success
        except Exception as e:
            logger.error(f"设置当前任务失败: {e}")
            return False

    def link_to_flow_session(self, task_id: str, flow_type: str = None, session_id: str = None) -> Optional[Dict[str, Any]]:
        """关联任务到工作流会话

        Args:
            task_id: 任务ID
            flow_type: 工作流类型，用于创建新会话
            session_id: 现有会话ID，用于关联到已有会话

        Returns:
            关联的会话信息，失败返回None
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
                    # 创建新会话
                    workflow_id = f"{flow_type}_workflow"  # 简化处理，实际应从配置或数据库获取
                    new_session = session_manager.create_session(
                        workflow_id=workflow_id, name=f"{flow_type}流程-{task_id[:8]}", task_id=task_id, flow_type=flow_type
                    )
                    session = new_session
                elif session_id:
                    # 关联到已有会话
                    session = session_manager.get_session(session_id)
                    if session:
                        # 更新会话关联到任务
                        session_manager.update_session(session.id, {"task_id": task_id})
                        # 设置为当前会话
                        session_manager.switch_session(session.id)

                if session:
                    # 更新任务的当前会话
                    self._db_service.task_repo.update_task(task_id, {"current_session_id": session.id})
                    # 设置当前任务
                    self.set_current_task(task_id)
                    return session.to_dict()
            return None
        except Exception as e:
            logger.error(f"关联任务到工作流会话失败: {e}")
            return None

    def create_task_with_flow(self, task_service, task_data: Dict[str, Any], workflow_id: str) -> Optional[Dict[str, Any]]:
        """创建任务并自动关联工作流会话

        Args:
            task_service: 任务服务实例
            task_data: 任务数据
            workflow_id: 工作流定义ID

        Returns:
            创建的任务数据，包含关联的工作流会话信息
        """
        try:
            # 1. 创建任务
            task = task_service.create_task(task_data["title"], task_data.get("story_id"), task_data.get("github_issue"))
            if not task:
                raise ValueError("创建任务失败")

            # 2. 创建工作流会话
            from src.flow_session.core.session_create import handle_create_session

            session_result = handle_create_session(
                workflow_id=workflow_id, name=f"Flow for {task['title']}", task_id=task["id"], verbose=False, agent_mode=True
            )

            if not session_result["success"]:
                error_msg = session_result.get("error_message", "创建工作流会话失败")
                raise ValueError(error_msg)

            # 3. 更新任务数据，添加会话信息
            task["flow_session"] = session_result["session"]

            # 4. 通过状态服务更新状态
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
        except Exception as e:
            logger.error(f"创建任务并关联工作流失败: {e}")
            return None

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

            db_session = get_session_factory()()  # 创建新的会话

            try:
                # 获取所有关联会话
                from src.db.repositories.flow_session_repository import FlowSessionRepository

                flow_repo = FlowSessionRepository(db_session)
                sessions = flow_repo.get_by_task_id(task_id)

                # 转换为字典格式
                return [session.to_dict() for session in sessions]
            finally:
                db_session.close()  # 确保关闭会话
        except Exception as e:
            logger.error(f"获取任务工作流会话失败: {e}")
            return []

    def get_current_task_session(self) -> Optional[Dict[str, Any]]:
        """获取当前任务的当前工作流会话

        Returns:
            当前工作流会话信息，如果不存在则返回None
        """
        try:
            # 尝试从状态服务获取当前任务信息
            task_status = self._status_service.get_domain_status("task")
            current_task = task_status.get("current_task")

            if not current_task:
                # 回退到直接获取当前任务
                from src.db import get_session_factory

                db_session = get_session_factory()()
                try:
                    task_repo = self._db_service.task_repo
                    task = task_repo.get_current_task()
                    current_task = task.to_dict() if task else None
                finally:
                    db_session.close()

                if not current_task:
                    return None

            # 获取当前任务的current_session_id
            session_id = current_task.get("current_session_id")
            if not session_id:
                return None

            # 尝试从状态服务获取工作流会话
            workflow_status = self._status_service.get_domain_status("workflow", f"flow-{session_id}")
            if workflow_status and "error" not in workflow_status:
                return workflow_status

            # 回退到直接获取会话
            from src.db import get_session_factory

            db_session = get_session_factory()()  # 创建新的会话

            try:
                # 创建FlowSessionManager实例
                from src.flow_session.manager import FlowSessionManager

                session_manager = FlowSessionManager(db_session)

                # 获取会话
                session = session_manager.get_session(session_id)
                return session.to_dict() if session else None
            finally:
                db_session.close()  # 确保关闭会话
        except Exception as e:
            logger.error(f"获取当前任务工作流会话失败: {e}")
            return None

    def set_current_task_session(self, session_id: str) -> bool:
        """设置当前任务的当前工作流会话

        Args:
            session_id: 会话ID

        Returns:
            操作是否成功
        """
        try:
            # 获取当前任务
            task_status = self._status_service.get_domain_status("task")
            current_task = task_status.get("current_task")

            if not current_task:
                # 回退到直接获取当前任务
                from src.db import get_session_factory

                db_session = get_session_factory()()
                try:
                    task_repo = self._db_service.task_repo
                    task = task_repo.get_current_task()
                    if not task:
                        logger.error("设置当前工作流会话失败: 当前没有活动任务")
                        return False
                    current_task = {"id": task.id}
                finally:
                    db_session.close()

            # 获取数据库会话
            from src.db import get_session_factory

            db_session = get_session_factory()()  # 创建新的会话

            try:
                # 验证会话是否存在
                from src.flow_session.manager import FlowSessionManager

                session_manager = FlowSessionManager(db_session)
                session = session_manager.get_session(session_id)

                if not session:
                    logger.error(f"设置当前工作流会话失败: 会话 {session_id} 不存在")
                    return False

                # 验证会话是否属于当前任务
                if session.task_id != current_task["id"]:
                    logger.error(f"设置当前工作流会话失败: 会话 {session_id} 不属于当前任务")
                    return False

                # 更新任务的current_session_id
                task_id = current_task["id"]
                from src.db.repositories.task_repository import TaskRepository

                task_repo = TaskRepository(db_session)
                task = task_repo.get_by_id(task_id)
                if not task:
                    logger.error(f"设置当前工作流会话失败: 任务 {task_id} 不存在")
                    return False

                task.current_session_id = session_id
                task_repo.update(task)
                db_session.commit()

                # 更新任务状态
                self._status_service.update_status(domain="task", entity_id=task_id, status=task.status, current_session_id=session_id)

                # 同时更新工作流状态
                self._status_service.update_status(domain="workflow", entity_id=f"flow-{session_id}", status="IN_PROGRESS")

                return True
            finally:
                db_session.close()  # 确保关闭会话
        except Exception as e:
            logger.error(f"设置当前工作流会话失败: {e}")
            return False
