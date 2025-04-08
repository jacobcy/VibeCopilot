"""
模板命令处理程序

提供模板相关命令的具体处理逻辑
"""

# 此模块已被拆分为多个子模块，现在只作为一个重定向导入器
# 所有功能现在由 handlers 包中的子模块提供

from src.templates.commands.template.handlers import (
    handle_template_create,
    handle_template_delete,
    handle_template_export,
    handle_template_generate,
    handle_template_import,
    handle_template_list,
    handle_template_load,
    handle_template_render,
    handle_template_show,
    handle_template_update,
)

# 导出所有处理程序函数，保持向后兼容性
__all__ = [
    "handle_template_list",
    "handle_template_show",
    "handle_template_import",
    "handle_template_create",
    "handle_template_update",
    "handle_template_delete",
    "handle_template_generate",
    "handle_template_load",
    "handle_template_export",
    "handle_template_render",
]
