"""
工作流会话状态集成核心类

提供工作流会话与状态系统的双向同步功能的核心实现。
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

# from src.db import FlowSessionRepository, WorkflowDefinitionRepository # 旧导入
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
from src.flow_session.status.status import SessionStatus
from src.models.db import FlowSession
from src.status.enums import StatusCategory, WorkflowStatus

# 会话状态到状态系统状态的映射
SESSION_STATUS_MAPPING = {
    SessionStatus.PENDING.value: "PENDING",
    SessionStatus.ACTIVE.value: "IN_PROGRESS",
    SessionStatus.PAUSED.value: "ON_HOLD",
    SessionStatus.COMPLETED.value: "COMPLETED",
    SessionStatus.FAILED.value: "FAILED",
}

# 状态系统状态到会话状态的映射
STATUS_SESSION_MAPPING = {
    "PENDING": SessionStatus.PENDING.value,
    "IN_PROGRESS": SessionStatus.ACTIVE.value,
    "ON_HOLD": SessionStatus.PAUSED.value,
    "COMPLETED": SessionStatus.COMPLETED.value,
    "FAILED": SessionStatus.FAILED.value,
    "CANCELED": SessionStatus.FAILED.value,  # 将CANCELED映射到FAILED状态
}


class FlowStatusIntegration:
    """工作流与状态系统的集成

    提供工作流会话与外部状态系统之间的双向同步功能。
    """

    def __init__(self, session: Session):
        """初始化

        Args:
            session: SQLAlchemy会话对象
        """
        self.session = session
        self.session_repo = FlowSessionRepository(session)
        self.workflow_repo = WorkflowDefinitionRepository(session)

    def map_session_to_status(self, flow_session: FlowSession) -> Dict[str, Any]:
        """将会话映射到状态系统的格式

        Args:
            flow_session: 工作流会话对象

        Returns:
            状态系统格式的任务数据
        """
        # 获取工作流定义
        workflow = self.workflow_repo.get_by_id(flow_session.workflow_id)
        workflow_name = workflow.name if workflow else "未知工作流"

        # 计算会话进度
        progress = self._calculate_session_progress(flow_session)

        return {
            "id": f"flow-{flow_session.id}",
            "name": flow_session.name,
            "type": "FLOW",
            "status": SESSION_STATUS_MAPPING.get(flow_session.status, "IN_PROGRESS"),
            "progress": progress,
            "created_at": flow_session.created_at.isoformat() if flow_session.created_at else None,
            "updated_at": flow_session.updated_at.isoformat() if flow_session.updated_at else None,
            "workflow_id": flow_session.workflow_id,
            "workflow_name": workflow_name,
            "current_stage": flow_session.current_stage_id,
            "metadata": {"flow_session_id": flow_session.id},
        }

    def _calculate_session_progress(self, flow_session: FlowSession) -> float:
        """计算会话进度

        Args:
            flow_session: 工作流会话对象

        Returns:
            进度百分比
        """
        if not flow_session.completed_stages:
            return 0.0

        # 获取工作流定义
        workflow = self.workflow_repo.get_by_id(flow_session.workflow_id)
        if not workflow or not workflow.stages:
            return 0.0

        total_stages = len(workflow.stages)
        completed_stages = len(flow_session.completed_stages or [])

        if total_stages == 0:
            return 0.0

        return round((completed_stages / total_stages) * 100, 2)

    def sync_session_to_status(self, session_id: str) -> Dict[str, Any]:
        """将会话状态同步到状态系统

        Args:
            session_id: 会话ID

        Returns:
            状态系统响应
        """
        flow_session = self.session_repo.get_by_id(session_id)
        if not flow_session:
            return {"error": "会话不存在", "success": False}

        status_data = self.map_session_to_status(flow_session)

        try:
            # 这里实际应该调用状态系统的API
            # status_api.update_task(status_data)

            # 模拟API调用成功
            return {"success": True, "task_id": status_data["id"], "status": status_data["status"]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sync_status_to_session(self, status_id: str) -> Dict[str, Any]:
        """从状态系统更新会话状态

        Args:
            status_id: 状态系统中的任务ID

        Returns:
            更新结果
        """
        # 从状态ID提取会话ID
        if not status_id.startswith("flow-"):
            return {"error": "无效的状态ID格式", "success": False}

        session_id = status_id[5:]  # 移除"flow-"前缀

        flow_session = self.session_repo.get_by_id(session_id)
        if not flow_session:
            return {"error": "会话不存在", "success": False}

        try:
            # 这里实际应该调用状态系统的API获取状态
            # status_data = status_api.get_task(status_id)

            # 模拟从状态系统获取数据
            status_data = {"id": status_id, "status": "IN_PROGRESS"}  # 假设从状态系统获取的状态

            # 映射状态
            new_status = STATUS_SESSION_MAPPING.get(status_data["status"])
            if new_status and new_status != flow_session.status:
                self.session_repo.update_status(session_id, new_status)

            return {"success": True, "session_id": session_id, "new_status": new_status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def register_session_change_hooks(self) -> Dict[str, Any]:
        """注册会话变更钩子

        注册监听器以在会话状态变更时自动同步到状态系统

        Returns:
            注册结果
        """
        # 这个方法应实际注册数据库或事件系统的钩子
        # 在此示例中，只返回成功信息
        return {"success": True, "message": "已注册会话变更钩子"}

    def create_status_for_session(self, session_id: str) -> Dict[str, Any]:
        """为新会话创建状态条目

        Args:
            session_id: 会话ID

        Returns:
            创建结果
        """
        flow_session = self.session_repo.get_by_id(session_id)
        if not flow_session:
            return {"error": "会话不存在", "success": False}

        status_data = self.map_session_to_status(flow_session)

        try:
            # 这里实际应该调用状态系统的API
            # status_api.create_task(status_data)

            # 模拟API调用成功
            return {"success": True, "task_id": status_data["id"], "status": status_data["status"]}
        except Exception as e:
            return {"success": False, "error": str(e)}
