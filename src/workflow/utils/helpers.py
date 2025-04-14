"""
工作流命令助手函数

提供格式化和辅助功能
"""

from typing import Any, Dict, List, Optional


def format_checklist(checklist: List[Dict[str, Any]]) -> str:
    """格式化检查清单，用于显示

    Args:
        checklist: 检查清单数据

    Returns:
        格式化后的文本
    """
    if not checklist:
        return "无检查项"

    result = ""
    for item in checklist:
        if isinstance(item, dict):
            item_id = item.get("id", "")
            item_name = item.get("name", item_id)
            result += f"\n  - {item_name}"
        else:
            result += f"\n  - {item}"

    return result


def format_deliverables(deliverables: List[Dict[str, Any]]) -> str:
    """格式化交付物，用于显示

    Args:
        deliverables: 交付物数据

    Returns:
        格式化后的文本
    """
    if not deliverables:
        return "无交付物"

    result = ""
    for item in deliverables:
        if isinstance(item, dict):
            item_id = item.get("id", "")
            item_name = item.get("name", item_id)
            result += f"\n  - {item_name}"
        else:
            result += f"\n  - {item}"

    return result


def format_workflow_steps(steps: List[Dict[str, Any]]) -> str:
    """格式化工作流步骤，用于显示

    Args:
        steps: 工作流步骤数据

    Returns:
        格式化后的文本
    """
    if not steps:
        return "无步骤"

    result = ""
    for idx, step in enumerate(steps):
        step_id = step.get("id", "")
        step_name = step.get("name", step_id)
        result += f"\n  {idx+1}. {step_name}"

        # 添加步骤描述(如果有)
        description = step.get("description")
        if description:
            result += f"\n     {description}"

    return result


def format_workflow_stages(stages: List[Dict[str, Any]]) -> str:
    """格式化工作流阶段，用于显示

    Args:
        stages: 工作流阶段数据

    Returns:
        格式化后的文本
    """
    if not stages:
        return "无阶段"

    result = ""
    for idx, stage in enumerate(stages):
        stage_id = stage.get("id", "")
        stage_name = stage.get("name", stage_id)
        result += f"\n  {idx+1}. {stage_name}"

        # 添加阶段描述(如果有)
        description = stage.get("description")
        if description:
            result += f"\n     {description}"

    return result
