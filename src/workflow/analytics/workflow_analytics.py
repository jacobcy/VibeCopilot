#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流分析模块

提供工作流的统计分析和进度跟踪功能。
"""

import logging
import os
from typing import Any, Dict, List, Optional

from src.core.config import get_config
from src.utils.file_utils import read_json_file
from src.workflow.operations import get_workflow, list_workflows

logger = logging.getLogger(__name__)


def get_workflow_executions(workflow_id: str) -> List[Dict[str, Any]]:
    """
    获取工作流的执行历史记录

    Args:
        workflow_id: 工作流ID

    Returns:
        List[Dict[str, Any]]: 执行历史记录列表
    """
    # 获取data_dir路径，确保配置正确访问
    data_dir = get_config().get("paths.data_dir", ".")
    executions_dir = os.path.join(data_dir, "workflow_executions")

    if not os.path.exists(executions_dir):
        return []

    executions = []

    # 查找匹配工作流ID的执行记录
    for filename in os.listdir(executions_dir):
        if filename.startswith(f"{workflow_id}_") and filename.endswith(".json"):
            execution_path = os.path.join(executions_dir, filename)
            try:
                execution_data = read_json_file(execution_path)
                executions.append(execution_data)
            except Exception as e:
                print(f"Error reading execution file {filename}: {str(e)}")

    # 按执行时间排序（从新到旧）
    executions.sort(key=lambda x: x.get("start_time", ""), reverse=True)

    return executions


def calculate_progress_statistics(workflow_id: Optional[str] = None) -> Dict[str, Any]:
    """
    计算工作流的进度统计信息

    Args:
        workflow_id: 可选，特定工作流ID。如果未提供，则计算所有工作流的统计信息

    Returns:
        Dict[str, Any]: 进度统计信息
    """
    all_workflows = []

    if workflow_id:
        # 获取特定工作流
        workflow = get_workflow(workflow_id)
        if workflow:
            all_workflows = [workflow]
    else:
        # 获取所有工作流
        all_workflows = list_workflows()

    if not all_workflows:
        return {"total_workflows": 0, "completed_workflows": 0, "in_progress_workflows": 0, "not_started_workflows": 0, "completion_rate": 0.0}

    # 初始化统计数据
    stats = {
        "total_workflows": len(all_workflows),
        "completed_workflows": 0,
        "in_progress_workflows": 0,
        "not_started_workflows": 0,
        "workflows_details": [],
    }

    # 分析每个工作流
    for workflow in all_workflows:
        workflow_stats = _analyze_workflow_progress(workflow)
        stats["workflows_details"].append(workflow_stats)

        if workflow_stats["status"] == "completed":
            stats["completed_workflows"] += 1
        elif workflow_stats["status"] == "in_progress":
            stats["in_progress_workflows"] += 1
        else:
            stats["not_started_workflows"] += 1

    # 计算完成率
    if stats["total_workflows"] > 0:
        stats["completion_rate"] = stats["completed_workflows"] / stats["total_workflows"]
    else:
        stats["completion_rate"] = 0.0

    return stats


def _analyze_workflow_progress(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析单个工作流的进度

    Args:
        workflow: 工作流数据

    Returns:
        Dict[str, Any]: 工作流进度信息
    """
    workflow_id = workflow.get("id")
    execution_history = get_workflow_executions(workflow_id)

    result = {
        "id": workflow_id,
        "name": workflow.get("name", "Unnamed Workflow"),
        "total_steps": len(workflow.get("steps", [])),
        "execution_count": len(execution_history),
        "last_execution": None,
        "status": "not_started",
    }

    # 检查是否有执行记录
    if execution_history:
        last_execution = execution_history[0]  # 最新的执行记录
        result["last_execution"] = {"time": last_execution.get("start_time"), "status": last_execution.get("status")}

        # 根据最后执行状态确定工作流状态
        if last_execution.get("status") == "completed":
            result["status"] = "completed"
        else:
            result["status"] = "in_progress"

    # 如果工作流有进度字段，使用它覆盖我们的计算
    if "progress" in workflow:
        result["progress"] = workflow["progress"]
        if workflow["progress"] >= 1.0:
            result["status"] = "completed"
        elif workflow["progress"] > 0:
            result["status"] = "in_progress"

    return result
