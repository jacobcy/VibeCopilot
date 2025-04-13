"""
工作流会话管理器核心类模块

提供FlowSessionManager类的核心功能定义。
注意：这是一个纯解释器，只负责解释和记录工作流程，不执行任何实际操作。
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.exceptions import EntityNotFoundError
from src.db import FlowSessionRepository, StageInstanceRepository, WorkflowDefinitionRepository
from src.models.db import FlowSession, StageInstance, WorkflowDefinition


class FlowSessionManager:
    """工作流会话管理器，处理会话的CRUD操作"""

    # 存储当前会话ID的文件路径
    CURRENT_SESSION_FILE = os.path.join(os.path.expanduser("~"), ".vibecopilot", "current_session.json")

    def __init__(self, session: Session, logger=None):
        """初始化

        Args:
            session: SQLAlchemy会话对象
            logger: 可选的日志记录器
        """
        self.session = session
        self.workflow_repo = WorkflowDefinitionRepository(session)
        self.session_repo = FlowSessionRepository(session)
        self.stage_repo = StageInstanceRepository(session)
        self._logger = logger

        # 确保存储当前会话ID的目录存在
        os.makedirs(os.path.dirname(self.CURRENT_SESSION_FILE), exist_ok=True)

    def set_logger(self, logger):
        """设置日志记录器

        Args:
            logger: 日志记录器实例
        """
        self._logger = logger

    def _log(self, method: str, *args, **kwargs):
        """内部日志记录方法

        Args:
            method: 要调用的日志方法名
            args: 位置参数
            kwargs: 关键字参数
        """
        if self._logger and hasattr(self._logger, method):
            getattr(self._logger, method)(*args, **kwargs)

    def create_session(
        self, workflow_id: str, session_name: Optional[str] = None, task_id: Optional[str] = None, name: Optional[str] = None
    ) -> FlowSession:
        """创建新的工作流会话

        Args:
            workflow_id: 工作流定义ID
            session_name: 可选，会话名称（兼容老接口）
            task_id: 可选，关联的任务ID
            name: 可选，会话名称

        Returns:
            创建的工作流会话，如果失败则返回None
        """
        # 创建新会话
        session_id = str(uuid.uuid4())
        context = {}  # 初始上下文为空

        # 优先使用name参数，兼容两种命名方式
        final_name = name or session_name or f"会话 {session_id[:8]}"

        new_session = FlowSession(id=session_id, workflow_id=workflow_id, name=final_name, status="ACTIVE", context=context, task_id=task_id)

        try:
            # 保存会话
            self.session.add(new_session)
            self.session.commit()

            # 设置为当前会话
            self._set_current_session(session_id)

            # 记录日志
            self._log("log_session_created", workflow_id, context)

            return new_session
        except IntegrityError as e:
            self.session.rollback()
            self._log("log_session_error", e)
            raise e

    def get_session(self, id_or_name: str) -> Optional[FlowSession]:
        """获取会话详情，支持通过ID或名称获取

        Args:
            id_or_name: 会话ID或名称

        Returns:
            会话对象或None
        """
        return self.session_repo.find_session_by_id_or_name(id_or_name)

    def list_sessions(self, status: Optional[str] = None, workflow_id: Optional[str] = None) -> List[FlowSession]:
        """列出会话，可按状态和工作流ID过滤

        Args:
            status: 会话状态
            workflow_id: 工作流ID

        Returns:
            会话列表
        """
        sessions = []
        if status and workflow_id:
            sessions = self.session_repo.get_by_workflow_and_status(workflow_id, status)
        elif status:
            sessions = self.session_repo.get_by_status(status)
        elif workflow_id:
            sessions = self.session_repo.get_by_workflow_id(workflow_id)
        else:
            sessions = self.session_repo.get_all()

        return sessions

    def update_session(self, id_or_name: str, data: Dict[str, Any]) -> Optional[FlowSession]:
        """更新会话数据，支持通过ID或名称更新

        Args:
            id_or_name: 会话ID或名称
            data: 更新数据

        Returns:
            更新后的会话对象或None

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        return self.session_repo.update(session.id, data)

    def delete_session(self, id_or_name: str) -> bool:
        """删除会话，支持通过ID或名称删除

        Args:
            id_or_name: 会话ID或名称

        Returns:
            是否删除成功

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 如果删除的是当前会话，清除当前会话设置
        current_session = self.get_current_session()
        if current_session and current_session.id == session.id:
            self._clear_current_session()

        return self.session_repo.delete(session.id)

    def update_session_status(self, id_or_name: str, new_status: str, reason: Optional[str] = None) -> Optional[FlowSession]:
        """更新会话状态

        Args:
            id_or_name: 会话ID或名称
            new_status: 新状态
            reason: 状态变更原因

        Returns:
            更新后的会话对象或None
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        old_status = session.status
        updated_session = self.session_repo.update_status(session.id, new_status)

        if updated_session:
            self._log("log_session_status_changed", old_status, new_status, reason)

        return updated_session

    def update_session_context(self, id_or_name: str, context: Dict[str, Any]) -> Optional[FlowSession]:
        """更新会话上下文

        Args:
            id_or_name: 会话ID或名称
            context: 上下文数据

        Returns:
            更新后的会话对象或None
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 合并现有上下文和新上下文
        current_context = session.context or {}
        current_context.update(context)

        updated_session = self.session_repo.update_context(session.id, current_context)

        if updated_session:
            self._log("log_session_context_updated", context)

        return updated_session

    def close_session(self, id_or_name: str, reason: Optional[str] = None) -> Optional[FlowSession]:
        """关闭会话

        Args:
            id_or_name: 会话ID或名称
            reason: 关闭原因

        Returns:
            更新后的会话对象或None
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 如果关闭的是当前会话，清除当前会话设置
        current_session = self.get_current_session()
        if current_session and current_session.id == session.id:
            self._clear_current_session()

        updated_session = self.session_repo.update_status(session.id, "CLOSED")

        if updated_session:
            self._log("log_session_closed", reason)

        return updated_session

    def switch_session(self, id_or_name: str) -> FlowSession:
        """切换当前会话

        Args:
            id_or_name: 会话ID或名称

        Returns:
            切换后的会话对象

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 设置为当前会话
        self._set_current_session(session.id)

        self._log("log_session_switched", session.id)

        return session

    def get_current_session(self) -> Optional[FlowSession]:
        """获取当前会话

        Returns:
            当前会话对象或None
        """
        session_id = self._get_current_session_id()
        if not session_id:
            return None

        return self.get_session(session_id)

    def _set_current_session(self, session_id: str) -> None:
        """设置当前会话ID

        Args:
            session_id: 会话ID
        """
        try:
            with open(self.CURRENT_SESSION_FILE, "w") as f:
                json.dump({"session_id": session_id}, f)
        except Exception as e:
            self._log("log_error", f"设置当前会话失败: {str(e)}")

    def _get_current_session_id(self) -> Optional[str]:
        """获取当前会话ID

        Returns:
            当前会话ID或None
        """
        try:
            if os.path.exists(self.CURRENT_SESSION_FILE):
                with open(self.CURRENT_SESSION_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("session_id")
        except Exception as e:
            self._log("log_error", f"获取当前会话ID失败: {str(e)}")
        return None

    def _clear_current_session(self) -> None:
        """清除当前会话设置"""
        try:
            if os.path.exists(self.CURRENT_SESSION_FILE):
                os.remove(self.CURRENT_SESSION_FILE)
        except Exception as e:
            self._log("log_error", f"清除当前会话设置失败: {str(e)}")

    def get_session_progress(self, id_or_name: str) -> Dict[str, Any]:
        """获取会话进度信息

        Args:
            id_or_name: 会话ID或名称

        Returns:
            进度信息字典
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 获取工作流定义
        workflow = self.workflow_repo.get_by_id(session.workflow_id)
        if not workflow:
            raise ValueError(f"找不到工作流定义: {session.workflow_id}")

        # 获取阶段实例列表
        stages = self.stage_repo.get_by_session_id(session.id)

        # 计算进度
        total_stages = len(workflow.stages)
        completed_stages = len([s for s in stages if s.status == "COMPLETED"])
        failed_stages = len([s for s in stages if s.status == "FAILED"])
        pending_stages = total_stages - completed_stages - failed_stages

        # 计算百分比
        completion_percentage = (completed_stages / total_stages * 100) if total_stages > 0 else 0

        # 获取当前阶段信息
        current_stage = None
        if session.current_stage_id:
            current_stage = next((s for s in stages if s.id == session.current_stage_id), None)

        # 构建进度信息
        progress = {
            "session_id": session.id,
            "session_name": session.name,
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "status": session.status,
            "total_stages": total_stages,
            "completed_stages": completed_stages,
            "failed_stages": failed_stages,
            "pending_stages": pending_stages,
            "completion_percentage": round(completion_percentage, 2),
            "current_stage": {
                "id": current_stage.id if current_stage else None,
                "name": current_stage.name if current_stage else None,
                "status": current_stage.status if current_stage else None,
            }
            if current_stage
            else None,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        }

        return progress

    def get_session_stages(self, id_or_name: str) -> List[StageInstance]:
        """获取会话的所有阶段实例

        Args:
            id_or_name: 会话ID或名称

        Returns:
            阶段实例列表
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        return self.stage_repo.get_by_session_id(session.id)

    def pause_session(self, id_or_name: str) -> Optional[FlowSession]:
        """暂停会话

        Args:
            id_or_name: 会话ID或名称

        Returns:
            更新后的会话对象或None
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        updated_session = self.session_repo.update_status(session.id, "PAUSED")

        if updated_session:
            self._log("log_session_paused", session.id)

        return updated_session

    def resume_session(self, id_or_name: str) -> Optional[FlowSession]:
        """恢复会话

        Args:
            id_or_name: 会话ID或名称

        Returns:
            更新后的会话对象或None
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        updated_session = self.session_repo.update_status(session.id, "ACTIVE")

        if updated_session:
            self._log("log_session_resumed", session.id)

        return updated_session

    def complete_session(self, id_or_name: str) -> Optional[FlowSession]:
        """完成会话

        Args:
            id_or_name: 会话ID或名称

        Returns:
            更新后的会话对象或None
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        updated_session = self.session_repo.update_status(session.id, "COMPLETED")

        if updated_session:
            self._log("log_session_completed", session.id)

        return updated_session
