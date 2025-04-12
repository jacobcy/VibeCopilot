#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流搜索模块

提供工作流的搜索和模糊匹配功能。
"""

from typing import Any, Dict, Optional

from src.workflow.operations import get_workflow, get_workflow_by_id, get_workflow_by_name, list_workflows


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

    return None


def get_workflow_context(workflow_id: str, current_task_id: str = None) -> dict:
    """
    获取工作流上下文，包括元数据和执行记录

    Args:
        workflow_id (str): 工作流ID
        current_task_id (str, optional): 当前任务ID. 默认为None.

    Returns:
        dict: 包含工作流上下文的字典
    """
    # 导入这里以避免循环导入
    from src.workflow.execution.workflow_execution import get_executions_for_workflow

    # 获取工作流
    workflow = get_workflow_by_id(workflow_id)
    if not workflow:
        return {"error": f"Workflow with ID {workflow_id} not found"}

    # 获取工作流执行历史
    executions = get_executions_for_workflow(workflow_id)

    # 构建上下文
    context = {"workflow": workflow, "executions": executions, "current_task_id": current_task_id}

    return context
