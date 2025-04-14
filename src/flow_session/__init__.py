"""
工作流会话包

提供工作流会话的管理功能，包括会话创建、暂停、恢复、完成等。
"""

from src.flow_session.manager import (  # 会话CRUD操作; 会话状态管理; 会话上下文管理; 当前会话管理; 阶段相关操作; 会话CRUD操作; 会话状态管理; 会话上下文管理; 当前会话管理; 阶段相关操作
    FlowSessionManager,
    clear_session_context,
    close_session,
    complete_session,
    create_session,
    delete_session,
    get_current_session,
    get_next_stages,
    get_session,
    get_session_context,
    get_session_first_stage,
    get_session_progress,
    get_session_stages,
    list_sessions,
    pause_session,
    resume_session,
    set_current_session,
    set_current_stage,
    start_session,
    switch_session,
    update_session,
    update_session_context,
)
from src.flow_session.stage.manager import StageInstanceManager
from src.flow_session.status.integration import FlowStatusIntegration

__all__ = [
    "FlowSessionManager",
    "StageInstanceManager",
    "FlowStatusIntegration",
    # 会话CRUD操作
    "create_session",
    "get_session",
    "list_sessions",
    "update_session",
    "delete_session",
    # 会话状态管理
    "start_session",
    "pause_session",
    "resume_session",
    "complete_session",
    "close_session",
    # 会话上下文管理
    "get_session_context",
    "update_session_context",
    "clear_session_context",
    # 当前会话管理
    "get_current_session",
    "switch_session",
    "set_current_session",
    # 阶段相关操作
    "get_session_stages",
    "get_session_first_stage",
    "get_session_progress",
    "set_current_stage",
    "get_next_stages",
]
