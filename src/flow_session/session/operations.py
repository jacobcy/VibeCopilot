"""
工作流会话操作模块

提供工作流会话高级操作的功能实现。
"""

import logging
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from src.db import get_session_factory, init_db
from src.db.repositories import FlowSessionRepository
from src.flow_session.session.manager import FlowSessionManager
from src.flow_session.stage.manager import StageInstanceManager
from src.models.db import FlowSession, StageInstance, WorkflowDefinition

logger = logging.getLogger(__name__)


def get_db_session():
    """获取数据库会话"""
    init_db()  # 确保数据库已初始化
    SessionFactory = get_session_factory()
    return SessionFactory()


def create_session(
    session: Session,
    workflow_id: str,
    session_name: str = None,
    task_id: str = None,
) -> Dict:
    """创建一个新的工作流会话。

    Args:
        session: 数据库会话
        workflow_id: 工作流定义ID
        session_name: 可选，会话名称
        task_id: 可选，关联的任务ID

    Returns:
        Dict: 包含创建结果的字典
    """
    try:
        manager = FlowSessionManager(session)
        new_session = manager.create_session(workflow_id=workflow_id, session_name=session_name, task_id=task_id)
        return {"status": "success", "session_id": new_session.id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_session(session_id: str) -> Optional[FlowSession]:
    """获取会话

    Args:
        session_id: 会话ID

    Returns:
        会话对象或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.get_session(session_id)


def handle_list_sessions(status: Optional[str] = None, workflow_id: Optional[str] = None) -> List[FlowSession]:
    """列出会话

    Args:
        status: 会话状态
        workflow_id: 工作流ID

    Returns:
        会话列表
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.list_sessions(status, workflow_id)


def update_session(session_id: str, data: Dict[str, Any]) -> Optional[FlowSession]:
    """更新会话

    Args:
        session_id: 会话ID
        data: 更新数据

    Returns:
        更新后的会话或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.update_session(session_id, data)


def delete_session(session_id: str) -> bool:
    """删除会话

    Args:
        session_id: 会话ID

    Returns:
        是否删除成功
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.delete_session(session_id)


def pause_session(session_id: str) -> Optional[FlowSession]:
    """暂停会话

    Args:
        session_id: 会话ID

    Returns:
        更新后的会话或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        try:
            return manager.pause_session(session_id)
        except Exception as e:
            logger.error(f"暂停会话失败: {e}")
            return None


def resume_session(session_id: str) -> Optional[FlowSession]:
    """恢复会话

    Args:
        session_id: 会话ID

    Returns:
        恢复后的会话对象或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        try:
            return manager.resume_session(session_id)
        except Exception as e:
            logger.error(f"恢复会话失败: {e}")
            return None


def complete_session(session_id: str) -> Optional[FlowSession]:
    """完成会话

    Args:
        session_id: 会话ID

    Returns:
        更新后的会话或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        try:
            return manager.complete_session(session_id)
        except Exception as e:
            logger.error(f"完成会话失败: {e}")
            return None


def close_session(session_id: str, reason: Optional[str] = None) -> Optional[FlowSession]:
    """结束会话

    Args:
        session_id: 会话ID
        reason: 结束原因(可选)

    Returns:
        结束后的会话对象或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        try:
            return manager.close_session(session_id, reason)
        except Exception as e:
            logger.error(f"结束会话失败: {e}")
            return None


def get_session_stages(session_id: str) -> List[StageInstance]:
    """获取会话中的所有阶段实例

    Args:
        session_id: 会话ID

    Returns:
        阶段实例列表
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.stage_repo.get_by_session_id(session_id)


def get_session_progress(session_id: str) -> Dict[str, Any]:
    """获取会话进度信息

    Args:
        session_id: 会话ID

    Returns:
        包含进度信息的字典
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        flow_session = manager.get_session(session_id)
        if not flow_session:
            return {"error": "会话不存在"}

        workflow = manager.workflow_repo.get_by_id(flow_session.workflow_id)
        if not workflow:
            return {"error": "工作流定义不存在"}

        stages = manager.stage_repo.get_by_session_id(session_id)

        # 获取工作流中定义的所有阶段
        all_stages = workflow.stages or []

        # 构造进度信息
        completed_stages = []
        current_stage = None
        pending_stages = []

        # 计算每个阶段的状态
        for stage_def in all_stages:
            stage_id = stage_def.get("id")
            stage_name = stage_def.get("name", "未命名阶段")

            # 查找对应的阶段实例
            stage_instance = next((s for s in stages if s.stage_id == stage_id), None)

            if not stage_instance:
                # 阶段尚未开始
                pending_stages.append({"id": stage_id, "name": stage_name, "status": "PENDING"})
                continue

            stage_info = {
                "id": stage_id,
                "name": stage_name,
                "status": stage_instance.status,
                "started_at": stage_instance.started_at.isoformat() if stage_instance.started_at else None,
                "completed_at": stage_instance.completed_at.isoformat() if stage_instance.completed_at else None,
            }

            if stage_instance.status == "COMPLETED":
                completed_stages.append(stage_info)
            elif stage_instance.status == "ACTIVE":
                current_stage = stage_info
            else:
                pending_stages.append(stage_info)

        # 计算进度百分比
        total_stages = len(all_stages)
        completed_count = len(completed_stages)
        progress_percentage = (completed_count / total_stages) * 100 if total_stages > 0 else 0

        return {
            "completed_stages": completed_stages,
            "current_stage": current_stage,
            "pending_stages": pending_stages,
            "total_stages": total_stages,
            "completed_count": completed_count,
            "progress_percentage": progress_percentage,
        }


def get_current_session() -> Optional[FlowSession]:
    """获取当前活动会话

    Returns:
        当前会话对象或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        return manager.get_current_session()


def set_current_stage(session_id: str, stage_id: str) -> Optional[FlowSession]:
    """设置会话的当前阶段

    Args:
        session_id: 会话ID
        stage_id: 阶段ID

    Returns:
        更新后的会话或None
    """
    with get_db_session() as session:
        manager = FlowSessionManager(session)
        flow_session = manager.get_session(session_id)
        if not flow_session:
            logger.error(f"会话不存在: {session_id}")
            return None

        try:
            # 更新会话的当前阶段
            flow_session.current_stage_id = stage_id
            session.commit()
            session.refresh(flow_session)
            return flow_session
        except Exception as e:
            session.rollback()
            logger.error(f"设置当前阶段失败: {e}")
            return None
