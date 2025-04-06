#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流操作模块

导入各个细分操作模块，包含工作流的创建、查看、执行等核心操作函数。
"""

import logging

from src.workflow.operations.crud_operations import (
    create_workflow,
    delete_workflow,
    update_workflow,
)
from src.workflow.operations.execution_operations import execute_workflow, sync_n8n

# 导入各个细分操作模块
from src.workflow.operations.list_operations import list_workflows, view_workflow

# 配置日志
logger = logging.getLogger(__name__)

# 导出所有函数，使其可以从workflow_operations模块直接导入
__all__ = [
    "list_workflows",
    "view_workflow",
    "create_workflow",
    "update_workflow",
    "delete_workflow",
    "execute_workflow",
    "sync_n8n",
]
