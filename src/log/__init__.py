#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块

提供统一的日志记录功能，包括工作流日志、操作日志、任务结果、性能指标、错误日志和审计日志。
同时支持文件日志和数据库持久化。
"""

from .log_service import (  # 工作流日志; 操作日志; 任务结果日志; 性能指标日志; 错误日志; 审计日志
    get_operation_tasks,
    get_recent_errors,
    get_user_audit_logs,
    get_workflow_logs,
    get_workflow_operations,
    log_audit,
    log_error,
    log_operation_complete,
    log_operation_start,
    log_performance_metric,
    log_task_result,
    log_workflow_complete,
    log_workflow_start,
)

__all__ = [
    # 工作流日志
    "log_workflow_start",
    "log_workflow_complete",
    "get_workflow_logs",
    # 操作日志
    "log_operation_start",
    "log_operation_complete",
    "get_workflow_operations",
    # 任务结果日志
    "log_task_result",
    "get_operation_tasks",
    # 性能指标日志
    "log_performance_metric",
    # 错误日志
    "log_error",
    "get_recent_errors",
    # 审计日志
    "log_audit",
    "get_user_audit_logs",
]
