#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流高级操作

导入点，集成了工作流的多个高级功能模块。
"""

# 从各个子模块导入公共API
from src.workflow.analytics.workflow_analytics import calculate_progress_statistics, get_workflow_executions
from src.workflow.execution.workflow_execution import execute_workflow, get_executions_for_workflow, save_execution
from src.workflow.search.workflow_search import get_workflow_context, get_workflow_fuzzy

# 公共API
__all__ = [
    # 工作流分析功能
    "calculate_progress_statistics",
    "get_workflow_executions",
    # 工作流执行功能
    "execute_workflow",
    "get_executions_for_workflow",
    "save_execution",
    # 工作流搜索功能
    "get_workflow_fuzzy",
    "get_workflow_context",
]
