#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行日志适配器

将原工作流执行记录功能适配到新的日志系统，保持API兼容性。
"""

from typing import Any, Dict, List, Optional

from src.log import log_service


def save_execution(execution_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    保存工作流执行记录

    Args:
        execution_data: 工作流执行数据

    Returns:
        更新后的执行数据
    """
    execution_id = execution_data.get("execution_id")
    workflow_id = execution_data.get("workflow_id")

    if not execution_id or not workflow_id:
        raise ValueError("执行ID和工作流ID是必须的")

    # 检查是否已存在该执行记录
    existing = log_service.get_workflow_execution(execution_id)

    if not existing:
        # 首次创建执行记录
        context = execution_data.get("context", {})
        # 复制其他可能的元数据字段
        for key in ["trigger_type", "trigger_info", "input_data"]:
            if key in execution_data:
                context[key] = execution_data[key]

        # 开始新的执行记录
        log_service.start_workflow_execution(workflow_id=workflow_id, context=context, execution_id=execution_id)

    # 更新执行状态
    update_params = {
        "execution_id": execution_id,
        "status": execution_data.get("status"),
    }

    # 添加可选参数
    if "messages" in execution_data:
        update_params["messages"] = execution_data["messages"]

    if "task_results" in execution_data:
        update_params["task_results"] = execution_data["task_results"]

    # 处理完成状态
    if execution_data.get("status") in ["completed", "success", "failed", "error"]:
        success = execution_data.get("status") in ["completed", "success"]
        log_service.complete_workflow_execution(
            execution_id=execution_id, success=success, messages=execution_data.get("messages", []), end_time=execution_data.get("end_time")
        )
    else:
        # 普通更新
        log_service.update_workflow_execution(**update_params)

    # 返回最新的执行数据
    return log_service.get_workflow_execution(execution_id)


def get_executions_for_workflow(workflow_id: str) -> List[Dict[str, Any]]:
    """
    获取工作流的所有执行记录

    Args:
        workflow_id: 工作流ID

    Returns:
        执行记录列表
    """
    return log_service.get_workflow_executions(workflow_id)


def get_workflow_executions(workflow_id: str) -> List[Dict[str, Any]]:
    """
    获取工作流的所有执行记录（兼容性别名）

    Args:
        workflow_id: 工作流ID

    Returns:
        执行记录列表
    """
    return get_executions_for_workflow(workflow_id)


def get_execution_by_id(execution_id: str) -> Optional[Dict[str, Any]]:
    """
    通过ID获取执行记录

    Args:
        execution_id: 执行ID

    Returns:
        执行记录，未找到则返回None
    """
    return log_service.get_workflow_execution(execution_id)


def update_execution_status(
    execution_id: str, status: str, messages: Optional[List[str]] = None, task_results: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    更新执行状态

    Args:
        execution_id: 执行ID
        status: 执行状态
        messages: 执行消息列表
        task_results: 任务结果字典

    Returns:
        更新后的执行记录
    """
    update_params = {"execution_id": execution_id, "status": status}

    if messages:
        update_params["messages"] = messages

    if task_results:
        update_params["task_results"] = task_results

    # 处理完成状态
    if status in ["completed", "success", "failed", "error"]:
        success = status in ["completed", "success"]
        log_service.complete_workflow_execution(execution_id=execution_id, success=success, messages=messages or [])
    else:
        # 普通更新
        log_service.update_workflow_execution(**update_params)

    return log_service.get_workflow_execution(execution_id)
