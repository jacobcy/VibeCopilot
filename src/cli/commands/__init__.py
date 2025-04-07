"""
命令处理模块

所有命令实现需要在此导入，方便统一管理
"""

# 导入所有命令处理器
from src.cli.commands.db import DatabaseCommand
from src.cli.commands.memory.memory_command import MemoryCommand
from src.cli.commands.roadmap import (
    CreateCommand,
    RoadmapCommand,
    RoadmapListCommand,
    StoryCommand,
    SwitchCommand,
    SyncCommand,
    UpdateRoadmapCommand,
)
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
]
