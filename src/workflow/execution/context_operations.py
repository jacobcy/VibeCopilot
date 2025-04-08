#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流上下文操作

提供工作流上下文管理相关的功能，包括上下文获取、元数据处理等。
"""

import logging
from typing import Any, Dict, Optional

from src.workflow.execution.execution_operations import get_executions_for_workflow
from src.workflow.workflow_operations import get_workflow, get_workflow_by_id, get_workflow_by_name, get_workflow_by_type

logger = logging.getLogger(__name__)


def get_workflow_metadata(workflow_id: str, current_task_id: str = None) -> dict:
    """
    获取工作流的元数据和上下文

    Args:
        workflow_id (str): 工作流ID
        current_task_id (str, optional): 当前任务ID。默认为None。

    Returns:
        dict: 包含工作流上下文的字典
    """
    # 获取工作流
    workflow = get_workflow_by_id(workflow_id)
    if not workflow:
        logger.warning(f"未找到ID为 {workflow_id} 的工作流")
        return {"error": f"Workflow with ID {workflow_id} not found"}

    # 获取工作流执行历史
    executions = get_executions_for_workflow(workflow_id)

    # 构建上下文
    context = {"workflow": workflow, "executions": executions, "current_task_id": current_task_id}

    return context


def get_workflow_context(workflow_id: str, include_executions: bool = True) -> Dict[str, Any]:
    """
    获取工作流的完整上下文信息，用于执行环境

    Args:
        workflow_id: 工作流ID
        include_executions: 是否包含执行历史记录

    Returns:
        Dict[str, Any]: 工作流上下文信息
    """
    # 获取工作流数据
    workflow = get_workflow(workflow_id)
    if not workflow:
        logger.warning(f"未找到ID为 {workflow_id} 的工作流")
        return {"error": "workflow_not_found", "workflow_id": workflow_id}

    # 创建基本上下文
    context = {
        "workflow": workflow,
        "workflow_id": workflow_id,
        "workflow_name": workflow.get("name", ""),
        "workflow_type": workflow.get("type", ""),
        "steps": workflow.get("steps", []),
    }

    # 如果需要，添加执行历史
    if include_executions:
        context["executions"] = get_executions_for_workflow(workflow_id)

    return context


def get_workflow_fuzzy(identifier: str) -> Optional[Dict[str, Any]]:
    """
    通过模糊匹配查找工作流，支持ID、名称或部分匹配

    Args:
        identifier: 工作流ID、名称或部分匹配字符串

    Returns:
        Optional[Dict[str, Any]]: 工作流数据（字典形式）或None
    """
    # 尝试精确匹配ID
    workflow = get_workflow(identifier)
    if workflow:
        return workflow

    # 尝试精确匹配名称
    workflow = get_workflow_by_name(identifier)
    if workflow:
        return workflow

    # 进行模糊匹配
    workflows = list_workflows()

    # 先尝试ID部分匹配
    for workflow in workflows:
        if identifier.lower() in workflow.get("id", "").lower():
            return workflow

    # 然后尝试名称部分匹配
    for workflow in workflows:
        if identifier.lower() in workflow.get("name", "").lower():
            return workflow

    # 最后尝试描述匹配
    for workflow in workflows:
        if "description" in workflow and workflow["description"] and identifier.lower() in workflow["description"].lower():
            return workflow

    logger.warning(f"未找到匹配 '{identifier}' 的工作流")
    return None


def merge_workflow_context(base_context: Dict[str, Any], additional_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并工作流上下文

    Args:
        base_context: 基础上下文
        additional_context: 要合并的额外上下文

    Returns:
        Dict[str, Any]: 合并后的上下文
    """
    result = base_context.copy()

    for key, value in additional_context.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # 递归合并字典
            result[key] = merge_workflow_context(result[key], value)
        else:
            # 直接覆盖其他类型
            result[key] = value

    return result
