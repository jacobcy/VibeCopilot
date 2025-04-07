"""
工作流会话与状态系统集成模块 (向后兼容包装器)

提供工作流会话与状态系统的双向同步功能。
本模块为向后兼容提供，新代码应使用 src.flow_session.status 模块。
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

# 重新导出原模块常量
from src.flow_session.status.integration import (
    SESSION_STATUS_MAPPING,
    STATUS_SESSION_MAPPING,
    FlowStatusIntegration,
)
from src.flow_session.status.operations import create_status_for_session as _create_status
from src.flow_session.status.operations import register_session_change_hooks as _register_hooks
from src.flow_session.status.operations import sync_session_to_status as _sync_to
from src.flow_session.status.operations import sync_status_to_session as _sync_from

# 为保持向后兼容，直接重导出核心类
FlowStatusIntegration = FlowStatusIntegration


def create_status_for_session(session: Session, session_id: str) -> Dict[str, Any]:
    """为新会话创建状态条目 (向后兼容)

    Args:
        session: SQLAlchemy会话对象
        session_id: 会话ID

    Returns:
        创建结果
    """
    return _create_status(session, session_id)


def sync_session_to_status(session: Session, session_id: str) -> Dict[str, Any]:
    """将会话状态同步到状态系统 (向后兼容)

    Args:
        session: SQLAlchemy会话对象
        session_id: 会话ID

    Returns:
        状态系统响应
    """
    return _sync_to(session, session_id)


def sync_status_to_session(session: Session, status_id: str) -> Dict[str, Any]:
    """从状态系统更新会话状态 (向后兼容)

    Args:
        session: SQLAlchemy会话对象
        status_id: 状态系统中的任务ID

    Returns:
        更新结果
    """
    return _sync_from(session, status_id)


def register_session_change_hooks(session: Session) -> Dict[str, Any]:
    """注册会话变更钩子 (向后兼容)

    Args:
        session: SQLAlchemy会话对象

    Returns:
        注册结果
    """
    return _register_hooks(session)


# 导出所有公共API
__all__ = [
    "FlowStatusIntegration",
    "create_status_for_session",
    "sync_session_to_status",
    "sync_status_to_session",
    "register_session_change_hooks",
    "SESSION_STATUS_MAPPING",
    "STATUS_SESSION_MAPPING",
]
