"""
工作流会话包

提供工作流会话的管理功能，包括会话创建、暂停、恢复、完成等。
"""

from src.flow_session.cli.commands import register_commands
from src.flow_session.session import (
    close_session,
    complete_session,
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
from src.flow_session.session.manager import FlowSessionManager
from src.flow_session.stage.manager import StageInstanceManager
from src.flow_session.status.integration import FlowStatusIntegration

__all__ = [
    "FlowSessionManager",
    "StageInstanceManager",
    "FlowStatusIntegration",
    "create_session",
    "get_session",
    "list_sessions",
    "update_session",
    "delete_session",
    "pause_session",
    "resume_session",
    "complete_session",
    "close_session",
    "get_session_stages",
    "get_session_progress",
    "set_current_stage",
    "register_commands",
]
