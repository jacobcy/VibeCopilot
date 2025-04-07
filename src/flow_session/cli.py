"""
工作流会话命令行接口模块 (向下兼容包装器)

提供用于管理工作流会话的命令行接口。
此模块为了向下兼容而保留，新代码应直接使用 src.flow_session.cli.commands 模块。
"""

# 从新结构中导入所有内容
from src.flow_session.cli.commands import (
    abort_session,
    create_session,
    delete_session,
    list_sessions,
    pause_session,
    register_commands,
    resume_session,
    session_group,
    show_session,
)

# 导出所有内容以保持向下兼容性
__all__ = [
    "list_sessions",
    "show_session",
    "create_session",
    "pause_session",
    "resume_session",
    "abort_session",
    "delete_session",
    "session_group",
    "register_commands",
]

if __name__ == "__main__":
    """命令行入口点"""
    session_group()
