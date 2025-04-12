#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行模块

提供工作流执行历史记录和存储功能。
实际记录功能已迁移到src/log模块，此处保持API兼容性。
"""

from src.workflow.execution.log_adapter import (
    get_execution_by_id,
    get_executions_for_workflow,
    get_workflow_executions,
    save_execution,
    update_execution_status,
)

__all__ = ["get_executions_for_workflow", "save_execution", "get_workflow_executions", "get_execution_by_id", "update_execution_status"]
