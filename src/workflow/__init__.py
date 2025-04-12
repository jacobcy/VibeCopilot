#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流系统

提供工作流的创建、读取、更新、删除等管理功能，
以及工作流的进度跟踪等功能。
"""

from src.workflow.flow_cmd.workflow_creator import create_workflow_from_rule, create_workflow_from_template_with_vars
from src.workflow.operations import (
    create_workflow,
    delete_workflow,
    get_workflow,
    get_workflow_by_id,
    get_workflow_by_name,
    get_workflow_by_type,
    get_workflow_file_path,
    get_workflows_directory,
    list_workflows,
    update_workflow,
)

# 这个导入不再需要，从新模块导入
# from src.workflow.flow_cmd.workflow_runner import get_workflow_context
from src.workflow.workflow_advanced_operations import (
    calculate_progress_statistics,
    get_executions_for_workflow,
    get_workflow_context,
    get_workflow_executions,
    get_workflow_fuzzy,
    save_execution,
)
from src.workflow.workflow_template import (
    create_workflow_from_template,
    create_workflow_template,
    delete_workflow_template,
    get_workflow_template,
    list_workflow_templates,
    update_workflow_template,
)

__all__ = [
    "list_workflows",
    "get_workflow",
    "get_workflow_by_id",
    "get_workflow_by_name",
    "get_workflow_by_type",
    "create_workflow",
    "update_workflow",
    "delete_workflow",
    "get_workflows_directory",
    "get_workflow_file_path",
    "get_workflow_executions",
    "get_executions_for_workflow",
    "save_execution",
    "calculate_progress_statistics",
    "get_workflow_context",
    "get_workflow_fuzzy",
    "create_workflow_from_rule",
    "create_workflow_from_template_with_vars",
    "list_workflow_templates",
    "get_workflow_template",
    "create_workflow_template",
    "update_workflow_template",
    "delete_workflow_template",
    "create_workflow_from_template",
]
