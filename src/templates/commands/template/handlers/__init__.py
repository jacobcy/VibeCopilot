"""
模板命令处理程序包

提供模板相关命令的具体处理逻辑，按功能分类
"""

from src.templates.commands.template.handlers.basic_handlers import (
    handle_template_delete,
    handle_template_export,
    handle_template_list,
    handle_template_show,
)
from src.templates.commands.template.handlers.edit_handlers import (
    handle_template_create,
    handle_template_import,
    handle_template_load,
    handle_template_update,
)
from src.templates.commands.template.handlers.generate_handlers import handle_template_generate, handle_template_render

# 导出所有处理程序函数
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
