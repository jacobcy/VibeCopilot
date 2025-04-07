#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流命令处理函数模块

提供各种工作流命令的处理函数
"""

# 从各个模块导入处理函数
from src.cli.commands.flow.handlers.base_handlers import (
    format_stage_summary,
    format_workflow_summary,
)
from src.cli.commands.flow.handlers.context_handlers import handle_get_workflow_context
from src.cli.commands.flow.handlers.create_handlers import handle_create_workflow
from src.cli.commands.flow.handlers.export_handlers import handle_export_workflow
from src.cli.commands.flow.handlers.import_handlers import handle_import_workflow
from src.cli.commands.flow.handlers.list_handlers import handle_list_workflows
from src.cli.commands.flow.handlers.next_handlers import handle_next_stage
from src.cli.commands.flow.handlers.run_handlers import handle_run_workflow_stage
from src.cli.commands.flow.handlers.session_handlers import handle_session_command
from src.cli.commands.flow.handlers.show_handlers import handle_show_workflow
from src.cli.commands.flow.handlers.update_handlers import handle_update_workflow
from src.cli.commands.flow.handlers.visualize_handlers import handle_visualize_workflow

# 导出所有函数
__all__ = [
    "format_workflow_summary",
    "format_stage_summary",
    "handle_list_workflows",
    "handle_create_workflow",
    "handle_show_workflow",
    "handle_get_workflow_context",
    "handle_export_workflow",
    "handle_import_workflow",
    "handle_run_workflow_stage",
    "handle_session_command",
    "handle_next_stage",
    "handle_update_workflow",
    "handle_visualize_workflow",
]
