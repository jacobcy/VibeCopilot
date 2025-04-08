"""
CLI命令模块

提供各种命令行命令的实现
"""

from src.cli.commands.db_commands import add_db_commands, handle_db_command
from src.cli.commands.template_commands import add_template_commands, generate_template, handle_template_command, list_templates, show_template

# 命令注册表字典，存储命令名称和处理函数的映射
COMMAND_REGISTRY = {"mock": lambda args: {"success": True, "message": "Mock command executed", "args": args}}

# 导出命令函数
__all__ = [
    "add_db_commands",
    "handle_db_command",
    "add_template_commands",
    "handle_template_command",
    "generate_template",
    "list_templates",
    "show_template",
    "COMMAND_REGISTRY",
]
