#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流工具函数模块

提供各种工作流处理相关的辅助函数
"""

import json
import logging
import os
from typing import Any, Dict, List

from src.workflow.config import PROJECT_ROOT

logger = logging.getLogger(__name__)


def _find_workflow_rule_paths(workflow_name: str) -> list:
    """
    查找与特定工作流类型相关的规则文件路径

    Args:
        workflow_name: 工作流名称

    Returns:
        包含匹配规则文件路径的列表
    """
    rule_paths = []
    project_root = PROJECT_ROOT

    # 规则文件路径列表，按优先顺序
    possible_paths = [
        os.path.join(project_root, ".cursor", "rules", "flow-rules"),
        os.path.join(project_root, "flow-rules"),
    ]

    # 可能的文件名格式
    possible_filenames = [
        f"{workflow_name}.md",
        f"{workflow_name}.mdc",
        f"{workflow_name}-flow.md",
        f"{workflow_name}-flow.mdc",
        f"{workflow_name}_flow.md",
        f"{workflow_name}_flow.mdc",
    ]

    for dir_path in possible_paths:
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                filename_lower = filename.lower()
                for possible_name in possible_filenames:
                    if filename_lower == possible_name.lower():
                        rule_paths.append(os.path.join(dir_path, filename))

    return rule_paths


def _save_stage_instance(instance_id: str, instance_data: Dict[str, Any]) -> bool:
    """
    保存阶段实例数据到文件

    Args:
        instance_id: 实例ID
        instance_data: 实例数据

    Returns:
        保存是否成功
    """
    # 创建实例存储目录
    instance_dir = os.path.join(PROJECT_ROOT, ".workflow", "instances")
    os.makedirs(instance_dir, exist_ok=True)

    # 保存实例数据
    instance_path = os.path.join(instance_dir, f"{instance_id}.json")
    try:
        with open(instance_path, "w", encoding="utf-8") as f:
            json.dump(instance_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存阶段实例失败: {str(e)}")
        return False


def _format_checklist(checklist: List[str]) -> str:
    """
    格式化检查清单

    Args:
        checklist: 检查清单项列表

    Returns:
        格式化后的字符串
    """
    if not checklist:
        return "  (无检查项)"

    return "\n".join([f"  □ {item}" for item in checklist])


def _format_deliverables(deliverables: List[str]) -> str:
    """
    格式化交付物

    Args:
        deliverables: 交付物列表

    Returns:
        格式化后的字符串
    """
    if not deliverables:
        return "  (无具体交付物)"

    return "\n".join([f"  • {item}" for item in deliverables])
