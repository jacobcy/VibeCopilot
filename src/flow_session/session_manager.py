"""
工作流会话管理器模块 (向下兼容包装器)

提供工作流会话的创建、查询、更新和删除功能。
此模块为了向下兼容而保留，新代码应直接使用 src.flow_session.session.manager 模块。
"""

from src.flow_session.session.manager import FlowSessionManager
from src.flow_session.session.operations import (
    abort_session,
    complete_session,
    complete_stage,
    create_session,
    delete_session,
    get_session,
    get_session_progress,
    get_session_stages,
    list_sessions,
    pause_session,
    resume_session,
    set_current_stage,
    update_session,
)

# 导出所有内容以保持向下兼容性
__all__ = [
    "FlowSessionManager",
    "create_session",
    "get_session",
    "list_sessions",
    "update_session",
    "delete_session",
    "pause_session",
    "resume_session",
    "complete_session",
    "abort_session",
    "get_session_stages",
    "get_session_progress",
    "set_current_stage",
    "complete_stage",
]
