"""
工作流会话状态集成便捷操作函数

提供用于与状态系统集成的便捷操作函数。
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.flow_session.status.integration import FlowStatusIntegration


def create_status_for_session(session: Session, session_id: str) -> Dict[str, Any]:
    """为新会话创建状态条目

    Args:
        session: SQLAlchemy会话对象
        session_id: 会话ID

    Returns:
        创建结果
    """
    integration = FlowStatusIntegration(session)
    return integration.create_status_for_session(session_id)


def sync_session_to_status(session: Session, session_id: str) -> Dict[str, Any]:
    """将会话状态同步到状态系统

    Args:
        session: SQLAlchemy会话对象
        session_id: 会话ID

    Returns:
        状态系统响应
    """
    integration = FlowStatusIntegration(session)
    return integration.sync_session_to_status(session_id)


def sync_status_to_session(session: Session, status_id: str) -> Dict[str, Any]:
    """从状态系统更新会话状态

    Args:
        session: SQLAlchemy会话对象
        status_id: 状态系统中的任务ID

    Returns:
        更新结果
    """
    integration = FlowStatusIntegration(session)
    return integration.sync_status_to_session(status_id)


def register_session_change_hooks(session: Session) -> Dict[str, Any]:
    """注册会话变更钩子

    注册监听器以在会话状态变更时自动同步到状态系统

    Args:
        session: SQLAlchemy会话对象

    Returns:
        注册结果
    """
    integration = FlowStatusIntegration(session)
    return integration.register_session_change_hooks()


def map_session_to_status_format(session: Session, session_id: str) -> Optional[Dict[str, Any]]:
    """将会话对象映射到状态系统的格式

    Args:
        session: SQLAlchemy会话对象
        session_id: 会话ID

    Returns:
        状态系统格式的任务数据，如果会话不存在则返回None
    """
    integration = FlowStatusIntegration(session)
    from src.db import FlowSessionRepository

    repo = FlowSessionRepository(session)
    flow_session = repo.get_by_id(session_id)

    if not flow_session:
        return None

    return integration.map_session_to_status(flow_session)


def get_session_progress(session: Session, session_id: str) -> Optional[float]:
    """获取会话的进度百分比

    Args:
        session: SQLAlchemy会话对象
        session_id: 会话ID

    Returns:
        进度百分比，如果会话不存在则返回None
    """
    integration = FlowStatusIntegration(session)
    from src.db import FlowSessionRepository

    repo = FlowSessionRepository(session)
    flow_session = repo.get_by_id(session_id)

    if not flow_session:
        return None

    return integration._calculate_session_progress(flow_session)
