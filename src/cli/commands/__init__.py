"""
命令处理模块

所有命令实现需要在此导入，方便统一管理
"""

# 导入所有命令处理器
from src.cli.commands.db import DatabaseCommand
from src.cli.commands.roadmap import (
    CheckRoadmapCommand,
    PlanCommand,
    RoadmapListCommand,
    StoryCommand,
    SwitchCommand,
    SyncCommand,
    UpdateRoadmapCommand,
)
from src.cli.commands.roadmap_commands import RoadmapCommands
from src.cli.commands.rule_command import RuleCommand

# TODO: 添加其他命令处理器

# 暴露所有命令处理器类
__all__ = [
    "DatabaseCommand",
    "RuleCommand",
    "CheckRoadmapCommand",
    "UpdateRoadmapCommand",
    "SyncCommand",
    "PlanCommand",
    "StoryCommand",
    "SwitchCommand",
    "RoadmapListCommand",
    "RoadmapCommands",
]
