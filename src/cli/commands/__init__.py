"""
VibeCopilot CLI命令包

包含所有CLI命令的实现。每个命令都是一个Click命令组。
"""

from src.cli.commands.db.db_click import db
from src.cli.commands.flow.flow_click import flow
from src.cli.commands.help.help_click import help
from src.cli.commands.memory.memory_click import memory
from src.cli.commands.roadmap.roadmap_click import roadmap
from src.cli.commands.rule.rule_click import rule
from src.cli.commands.status.status_click import status
from src.cli.commands.task.task_click import task
from src.cli.commands.template.template_click import template

__all__ = [
    "db",
    "flow",
    "help",
    "memory",
    "roadmap",
    "rule",
    "status",
    "task",
    "template",
]

# 所有Click命令组
CLICK_COMMANDS = [
    db,
    flow,
    help,
    memory,
    roadmap,
    rule,
    status,
    task,
    template,
]

# 旧版命令（如果需要兼容）
OLD_COMMANDS = {}

# 命令注册表
COMMAND_REGISTRY = {
    "db": db,
    "flow": flow,
    "help": help,
    "memory": memory,
    "roadmap": roadmap,
    "rule": rule,
    "status": status,
    "task": task,
    "template": template,
}
