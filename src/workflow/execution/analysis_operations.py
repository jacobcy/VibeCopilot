#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流分析操作

提供工作流执行分析相关的功能，包括进度统计、性能分析等。
"""

import logging
from typing import Any, Dict, List, Optional

from src.workflow.execution.execution_operations import get_workflow_executions
from src.workflow.workflow_operations import get_workflow, list_workflows

logger = logging.getLogger(__name__)


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
            logger.warning(f"未找到ID为 {workflow_id} 的工作流")
    else:
        # 获取所有工作流
        all_workflows = list_workflows()

    if not all_workflows:
        logger.info("没有找到需要分析的工作流")
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


def calculate_performance_metrics(workflow_id: str) -> Dict[str, Any]:
    """
    计算工作流的性能指标

    Args:
        workflow_id: 工作流ID

    Returns:
        Dict[str, Any]: 工作流性能指标
    """
    executions = get_workflow_executions(workflow_id)

    if not executions:
        logger.info(f"工作流 {workflow_id} 没有执行记录，无法计算性能指标")
        return {"workflow_id": workflow_id, "execution_count": 0, "metrics": {}}

    # 初始化指标
    metrics = {
        "workflow_id": workflow_id,
        "execution_count": len(executions),
        "success_rate": 0,
        "average_duration": 0,
        "fastest_execution": None,
        "slowest_execution": None,
        "metrics_by_step": {},
    }

    # 计算成功率和其他指标
    successful_executions = [e for e in executions if e.get("status") == "completed"]
    if executions:
        metrics["success_rate"] = len(successful_executions) / len(executions)

    # 计算执行时间（只考虑已完成的执行）
    completed_with_times = []
    for execution in executions:
        if execution.get("status") in ["completed", "failed"] and "start_time" in execution and "end_time" in execution:
            try:
                start_time = execution["start_time"]
                end_time = execution["end_time"]
                # 计算持续时间（实际实现中需要解析ISO时间格式）
                duration = end_time - start_time  # 简化示例
                execution["duration"] = duration
                completed_with_times.append(execution)
            except Exception as e:
                logger.error(f"计算执行时间出错: {e}")

    # 如果有完整时间记录的执行
    if completed_with_times:
        # 计算平均时间
        total_duration = sum(e["duration"] for e in completed_with_times)
        metrics["average_duration"] = total_duration / len(completed_with_times)

        # 找出最快和最慢的执行
        fastest = min(completed_with_times, key=lambda e: e["duration"])
        slowest = max(completed_with_times, key=lambda e: e["duration"])

        metrics["fastest_execution"] = {"execution_id": fastest["execution_id"], "duration": fastest["duration"], "start_time": fastest["start_time"]}

        metrics["slowest_execution"] = {"execution_id": slowest["execution_id"], "duration": slowest["duration"], "start_time": slowest["start_time"]}

    return metrics


def generate_workflow_report(workflow_id: str) -> Dict[str, Any]:
    """
    生成综合工作流报告

    Args:
        workflow_id: 工作流ID

    Returns:
        Dict[str, Any]: 工作流综合报告
    """
    # 获取工作流
    workflow = get_workflow(workflow_id)
    if not workflow:
        logger.warning(f"未找到ID为 {workflow_id} 的工作流")
        return {"error": "workflow_not_found", "workflow_id": workflow_id}

    # 获取进度统计
    progress_stats = calculate_progress_statistics(workflow_id)

    # 获取性能指标
    performance_metrics = calculate_performance_metrics(workflow_id)

    # 组合报告
    report = {
        "workflow_id": workflow_id,
        "workflow_name": workflow.get("name", ""),
        "workflow_type": workflow.get("type", ""),
        "created_at": workflow.get("created_at", ""),
        "updated_at": workflow.get("updated_at", ""),
        "progress": progress_stats.get("workflows_details", [{}])[0] if progress_stats.get("workflows_details") else {},
        "performance": performance_metrics,
        "summary": {
            "status": progress_stats.get("workflows_details", [{}])[0].get("status", "unknown")
            if progress_stats.get("workflows_details")
            else "unknown",
            "execution_count": performance_metrics.get("execution_count", 0),
            "success_rate": performance_metrics.get("success_rate", 0),
            "average_duration": performance_metrics.get("average_duration", 0),
        },
    }

    return report
