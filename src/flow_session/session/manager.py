"""
工作流会话管理器核心类模块

提供FlowSessionManager类的核心功能定义。
"""

import json
import logging
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

# 创建日志记录器
logger = logging.getLogger(__name__)


class FlowSessionManager:
    """工作流会话管理器，处理会话的CRUD操作"""

    # 存储当前会话ID的文件路径
    CURRENT_SESSION_FILE = os.path.join(os.path.expanduser("~"), ".vibecopilot", "current_session.json")

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        self.session = session
        self.workflow_repo = WorkflowDefinitionRepository(session)
        self.session_repo = FlowSessionRepository(session)
        self.stage_repo = StageInstanceRepository(session)

        # 确保存储当前会话ID的目录存在
        os.makedirs(os.path.dirname(self.CURRENT_SESSION_FILE), exist_ok=True)

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
        logger.debug(f"Creating new flow session for workflow {workflow_id}")
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

            return new_session
        except IntegrityError as e:
            self.session.rollback()
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
        logger.debug(f"FlowSessionManager.list_sessions() 被调用，参数: status={status}, workflow_id={workflow_id}")
        sessions = []
        if status and workflow_id:
            sessions = self.session_repo.get_by_workflow_and_status(workflow_id, status)
        elif status:
            sessions = self.session_repo.get_by_status(status)
        elif workflow_id:
            sessions = self.session_repo.get_by_workflow_id(workflow_id)
        else:
            sessions = self.session_repo.get_all()

        logger.debug(f"获取到 {len(sessions)} 个会话对象")
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

    def close_session(self, id_or_name: str, reason: Optional[str] = None) -> Optional[FlowSession]:
        """结束会话（替代abort_session），支持通过ID或名称操作

        Args:
            id_or_name: 会话ID或名称
            reason: 结束原因（可选）

        Returns:
            更新后的会话对象或None

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 如果提供了原因，更新会话上下文
        if reason:
            context = dict(session.context or {})
            context["close_reason"] = reason
            self.session_repo.update_context(session.id, context)

        return self.session_repo.update_status(session.id, "CLOSED")

    def update_session_context(self, id_or_name: str, context: Dict[str, Any]) -> Optional[FlowSession]:
        """更新会话上下文，支持通过ID或名称操作

        Args:
            id_or_name: 会话ID或名称
            context: 上下文数据

        Returns:
            更新后的会话对象或None

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        return self.session_repo.update_context(session.id, context)

    def switch_session(self, id_or_name: str) -> FlowSession:
        """切换当前活动会话

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

        # 确保会话处于活动状态
        if session.status != "ACTIVE":
            # 如果会话不是活动状态，将其激活
            self.session_repo.update_status(session.id, "ACTIVE")

        # 将会话设置为当前会话
        self._set_current_session(session.id)

        return session

    def get_current_session(self) -> Optional[FlowSession]:
        """获取当前活动会话

        Returns:
            当前会话对象或None（如果没有设置当前会话）
        """
        session_id = self._get_current_session_id()
        if not session_id:
            return None

        return self.session_repo.get_by_id(session_id)

    def _set_current_session(self, session_id: str) -> None:
        """设置当前会话ID

        Args:
            session_id: 会话ID
        """
        try:
            with open(self.CURRENT_SESSION_FILE, "w") as f:
                json.dump({"current_session_id": session_id}, f)
        except Exception as e:
            print(f"[警告] 无法保存当前会话ID: {str(e)}")

    def _get_current_session_id(self) -> Optional[str]:
        """获取当前会话ID

        Returns:
            当前会话ID或None
        """
        try:
            if os.path.exists(self.CURRENT_SESSION_FILE):
                with open(self.CURRENT_SESSION_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("current_session_id")
        except Exception as e:
            print(f"[警告] 无法读取当前会话ID: {str(e)}")

        return None

    def _clear_current_session(self) -> None:
        """清除当前会话设置"""
        try:
            if os.path.exists(self.CURRENT_SESSION_FILE):
                os.remove(self.CURRENT_SESSION_FILE)
        except Exception as e:
            print(f"[警告] 无法清除当前会话设置: {str(e)}")

    def get_session_progress(self, id_or_name: str) -> Dict[str, Any]:
        """获取会话的进度信息

        Args:
            id_or_name: 会话ID或名称

        Returns:
            包含会话进度信息的字典，包括已完成阶段、当前阶段和待进行阶段

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 获取工作流定义
        workflow = self.workflow_repo.get_by_id(session.workflow_id)
        if not workflow:
            # 可能是工作流已被删除
            return {
                "completed_stages": [],
                "current_stage": None,
                "pending_stages": [],
                "total_stages": 0,
                "completed_count": 0,
                "progress_percentage": 0,
            }

        # 获取工作流的所有阶段
        stages = workflow.stages if hasattr(workflow, "stages") and workflow.stages else []
        if isinstance(stages, str):
            try:
                # 如果stages是JSON字符串，解析它
                stages = json.loads(stages)
            except:
                stages = []

        # 如果stages是字典而不是列表，转换它
        if isinstance(stages, dict):
            stages = [{"id": k, "name": v.get("name", k)} for k, v in stages.items()]

        # 已完成阶段、当前阶段和待进行阶段
        completed_stages = []
        current_stage = None
        pending_stages = []

        # 获取会话关联的阶段实例
        stage_instances = self.get_session_stages(session.id)

        # 从阶段实例构建已完成阶段列表
        for stage_instance in stage_instances:
            stage_info = next((s for s in stages if s.get("id") == stage_instance.stage_id), None)
            if not stage_info:
                continue

            stage_data = {
                "id": stage_instance.stage_id,
                "name": stage_info.get("name", stage_instance.stage_id),
                "started_at": stage_instance.started_at.isoformat() if stage_instance.started_at else None,
                "completed_at": stage_instance.completed_at.isoformat() if stage_instance.completed_at else None,
                "status": stage_instance.status,
            }

            if stage_instance.status == "COMPLETED":
                completed_stages.append(stage_data)
            elif stage_instance.status == "ACTIVE":
                current_stage = stage_data

        # 构建待进行阶段列表
        if stages:
            # 查找所有未开始的阶段
            for stage in stages:
                stage_id = stage.get("id")
                if stage_id not in [s.stage_id for s in stage_instances]:
                    pending_stages.append({"id": stage_id, "name": stage.get("name", stage_id)})

        # 计算进度百分比
        total_stages = len(stages)
        completed_count = len(completed_stages)
        progress_percentage = (completed_count / total_stages * 100) if total_stages > 0 else 0

        return {
            "completed_stages": completed_stages,
            "current_stage": current_stage,
            "pending_stages": pending_stages,
            "total_stages": total_stages,
            "completed_count": completed_count,
            "progress_percentage": round(progress_percentage, 2),
        }

    def get_session_stages(self, id_or_name: str) -> List[StageInstance]:
        """获取会话关联的所有阶段实例

        Args:
            id_or_name: 会话ID或名称

        Returns:
            阶段实例列表

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        # 使用阶段实例仓库查询
        return self.stage_repo.get_by_session_id(session.id)

    def pause_session(self, id_or_name: str) -> Optional[FlowSession]:
        """暂停会话，支持通过ID或名称操作

        Args:
            id_or_name: 会话ID或名称

        Returns:
            更新后的会话对象或None

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        return self.session_repo.update_status(session.id, "PAUSED")

    def resume_session(self, id_or_name: str) -> Optional[FlowSession]:
        """恢复会话，支持通过ID或名称操作

        Args:
            id_or_name: 会话ID或名称

        Returns:
            更新后的会话对象或None

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        return self.session_repo.update_status(session.id, "ACTIVE")

    def complete_session(self, id_or_name: str) -> Optional[FlowSession]:
        """完成会话，支持通过ID或名称操作

        Args:
            id_or_name: 会话ID或名称

        Returns:
            更新后的会话对象或None

        Raises:
            ValueError: 如果找不到指定的会话
        """
        session = self.get_session(id_or_name)
        if not session:
            raise ValueError(f"找不到会话: {id_or_name}")

        return self.session_repo.update_status(session.id, "COMPLETED")
