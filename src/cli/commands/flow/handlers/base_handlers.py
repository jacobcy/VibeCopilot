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

    summary = [
        f"工作流: {workflow.get('name', '未命名')}",
        f"ID: {workflow.get('id', '无ID')}",
        f"描述: {workflow.get('description', '无描述')}",
        f"来源: {workflow.get('source_rule', '未知来源')}",
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
