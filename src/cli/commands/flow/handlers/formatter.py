#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流基础处理函数

提供工作流处理的基础工具函数和格式化函数
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def format_workflow_summary(workflow: Dict[str, Any]) -> str:
    """
    格式化工作流摘要

    Args:
        workflow: 工作流数据

    Returns:
        格式化后的摘要文本
    """
    if not workflow:
        return "无效的工作流"

    # 获取来源信息
    metadata = workflow.get("metadata", {})
    source = metadata.get("source_example", workflow.get("source_rule", "未知来源"))

    summary = [
        f"工作流: {workflow.get('name', '未命名')}",
        f"ID: {workflow.get('id', '无ID')}",
        f"描述: {workflow.get('description', '无描述')}",
        f"来源: {source}",
        f"版本: {workflow.get('version', '1.0.0')}",
        f"阶段数: {len(workflow.get('stages', []))}",
        f"转换数: {len(workflow.get('transitions', []))}",
    ]

    return "\n".join(summary)


def format_stage_summary(stage: Dict[str, Any], completed_items: List[str] = None) -> str:
    """
    格式化阶段摘要

    Args:
        stage: 阶段数据
        completed_items: 已完成的检查项

    Returns:
        格式化后的摘要文本
    """
    if not stage:
        return "无效的阶段"

    completed_items = completed_items or []

    summary = [
        f"阶段: {stage.get('name', '未命名')}",
        f"描述: {stage.get('description', '无描述')}",
        f"顺序: {stage.get('order', 0)}",
        "",
    ]

    # 添加检查清单
    if stage.get("checklist"):
        summary.append("📋 检查清单:")
        for item in stage.get("checklist", []):
            status = "✅" if item in completed_items else "⬜"
            summary.append(f"{status} {item}")
        summary.append("")

    # 添加交付物
    if stage.get("deliverables"):
        summary.append("📦 交付物:")
        for item in stage.get("deliverables", []):
            summary.append(f"📄 {item}")

    return "\n".join(summary)


def format_session_summary(session: Dict[str, Any], verbose: bool = False) -> str:
    """
    格式化工作流会话摘要

    Args:
        session: 会话数据
        verbose: 是否显示详细信息

    Returns:
        格式化后的摘要文本
    """
    if not session:
        return "无效的会话"

    # 基本会话信息
    summary = [
        f"会话: {session.get('name', '未命名')}",
        f"ID: {session.get('id', '无ID')}",
        f"状态: {session.get('status', '未知状态')}",
        f"工作流: {session.get('workflow_id', '未知工作流')}",
    ]

    # 当前阶段信息
    current_stage = session.get("current_stage_id")
    if current_stage:
        summary.append(f"当前阶段: {current_stage}")

    # 任务关联信息
    task_id = session.get("task_id")
    if task_id:
        task_title = session.get("task_title", task_id)
        summary.append(f"关联任务: {task_title} (ID: {task_id})")

    # 时间信息
    created_at = session.get("created_at")
    if created_at:
        summary.append(f"创建时间: {created_at}")

    updated_at = session.get("updated_at")
    if updated_at:
        summary.append(f"更新时间: {updated_at}")

    # 如果要显示详细信息
    if verbose:
        # 添加已完成阶段
        completed_stages = session.get("completed_stages", [])
        if completed_stages:
            summary.append("\n已完成阶段:")
            for stage in completed_stages:
                if isinstance(stage, dict):
                    stage_name = stage.get("name", stage.get("id", "未知阶段"))
                    summary.append(f"  ✅ {stage_name}")
                else:
                    summary.append(f"  ✅ {stage}")

        # 添加上下文信息
        context = session.get("context")
        if context:
            summary.append("\n上下文信息:")
            if isinstance(context, dict):
                for key, value in context.items():
                    summary.append(f"  {key}: {value}")
            else:
                summary.append(f"  {context}")

    return "\n".join(summary)


def format_session_list(sessions: List[Dict[str, Any]], verbose: bool = False) -> str:
    """
    格式化工作流会话列表

    Args:
        sessions: 会话列表
        verbose: 是否显示详细信息

    Returns:
        格式化后的会话列表文本
    """
    if not sessions:
        return "当前没有工作流会话"

    summary = ["工作流会话列表:", ""]

    for i, session in enumerate(sessions, 1):
        # 简洁模式下只显示基本信息
        if not verbose:
            task_info = ""
            if session.get("task_id"):
                task_title = session.get("task_title", "")
                task_info = f" - 任务: {task_title} ({session.get('task_id')})"

            summary.append(f"{i}. {session.get('name', '未命名')} (ID: {session.get('id', '无ID')}){task_info}")
        else:
            # 详细模式下显示完整摘要，并用分隔线分开每个会话
            session_summary = format_session_summary(session, verbose)
            summary.append(f"--- 会话 {i} ---")
            summary.append(session_summary)
            summary.append("")  # 空行分隔

    summary.append(f"\n共找到 {len(sessions)} 个会话")

    return "\n".join(summary)
