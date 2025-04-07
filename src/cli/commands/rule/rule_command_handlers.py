"""
规则命令处理函数

此模块重导出从handlers/目录中拆分的处理函数，以保持向后兼容性。
"""

# 从子模块重导出所有处理函数
from src.cli.commands.rule.handlers import (
    create_rule,
    delete_rule,
    edit_rule,
    export_rule,
    import_rule,
    list_rules,
    show_rule,
    validate_rule,
)

__all__ = [
    "create_rule",
    "list_rules",
    "show_rule",
    "edit_rule",
    "delete_rule",
    "validate_rule",
    "export_rule",
    "import_rule",
]
