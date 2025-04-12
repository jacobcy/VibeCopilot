#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流基础操作

提供工作流的基本管理功能，包括增删改查。

!!! 已弃用 !!!
此文件已被拆分为多个较小的文件，位于 src/workflow/operations/ 目录中。
请直接使用新的模块化结构:
    from src.workflow.operations import (
        get_workflows_directory, get_workflow_file_path,
        list_workflows, get_workflow, get_workflow_by_id, get_workflow_by_name,
        get_workflow_by_type, view_workflow, create_workflow, update_workflow,
        delete_workflow, validate_workflow_files, sync_workflow_to_db
    )
"""

import logging

# 导入文件工具函数，以便兼容旧代码
from src.utils.file_utils import ensure_directory_exists, read_json_file, write_json_file

# 从新的模块导入所有功能
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
    sync_workflow_to_db,
    update_workflow,
    validate_workflow_files,
    view_workflow,
)

# 设置兼容性警告
logger = logging.getLogger(__name__)
logger.debug("从 workflow_operations.py 导入已被弃用。请使用 'from src.workflow.operations import ...'。" "此兼容层将在将来的版本中移除。")

# 导出所有公开函数以保持向后兼容性
__all__ = [
    "get_workflows_directory",
    "get_workflow_file_path",
    "list_workflows",
    "get_workflow",
    "get_workflow_by_id",
    "get_workflow_by_name",
    "get_workflow_by_type",
    "view_workflow",
    "create_workflow",
    "update_workflow",
    "delete_workflow",
    "validate_workflow_files",
    "sync_workflow_to_db",
    # 文件工具函数，为了向后兼容
    "ensure_directory_exists",
    "write_json_file",
    "read_json_file",
]
