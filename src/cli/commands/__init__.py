"""
命令处理模块

所有命令实现需要在此导入，方便统一管理
"""

# 基本导入
from typing import Any, Callable, Dict, List

# 导入所有命令处理器
from src.cli.commands.db import DatabaseCommand
from src.cli.commands.flow.handlers.session_handlers import handle_session_command
from src.cli.commands.github.handlers import handle_github_command
from src.cli.commands.memory.memory_command import MemoryCommand
from src.cli.commands.roadmap import CreateCommand, RoadmapCommand, RoadmapListCommand, StoryCommand, SwitchCommand, SyncCommand, UpdateRoadmapCommand
from src.cli.commands.roadmap_commands import RoadmapCommands
from src.cli.commands.rule.rule_command import RuleCommand

# TODO: 添加其他命令处理器

# 暴露所有命令处理器类
__all__ = [
    "DatabaseCommand",
    "MemoryCommand",
    "RuleCommand",
    "UpdateRoadmapCommand",
    "SyncCommand",
    "CreateCommand",
    "StoryCommand",
    "SwitchCommand",
    "RoadmapListCommand",
    "RoadmapCommands",
    # Add commands from registration
    "handle_session_command",
    "handle_github_command",
]

"""
命令注册表

存储所有可用的命令处理器
"""

COMMAND_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = {
    "flow": handle_session_command,
    "github": handle_github_command,
    # 添加更多命令处理器
}
