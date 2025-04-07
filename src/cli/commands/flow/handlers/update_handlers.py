#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流更新处理模块

提供更新工作流定义的功能
"""

import json
import logging
from typing import Any, Dict, Optional, Tuple

from src.workflow.exporters.json_exporter import JsonExporter

logger = logging.getLogger(__name__)


def handle_update_workflow(
    workflow_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    verbose: bool = False,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理更新工作流命令

    Args:
        workflow_id: 工作流ID
        name: 新的工作流名称（可选）
        description: 新的工作流描述（可选）
        verbose: 是否显示详细信息

    Returns:
        包含状态、消息和更新后的工作流数据的元组
    """
    try:
        # 加载现有工作流
        exporter = JsonExporter()
        workflow = exporter.load_workflow(workflow_id)

        if not workflow:
            return False, f"找不到ID为 '{workflow_id}' 的工作流", None

        # 记录原始值用于日志
        original_name = workflow.get("name", "")
        original_desc = workflow.get("description", "")

        # 更新字段
        updated = False

        if name is not None and name.strip():
            workflow["name"] = name.strip()
            updated = True

        if description is not None and description.strip():
            workflow["description"] = description.strip()
            updated = True

        if not updated:
            return False, "未提供任何更新字段 (name 或 description)", None

        # 保存更新后的工作流
        exporter.export_workflow(workflow)

        # 准备响应消息
        changes = []
        if name is not None and name.strip() and name.strip() != original_name:
            changes.append(f"名称: '{original_name}' -> '{workflow['name']}'")

        if description is not None and description.strip() and description.strip() != original_desc:
            changes.append(f"描述: '{original_desc}' -> '{workflow['description']}'")

        message = f"✅ 工作流 '{workflow_id}' 已更新\n\n"
        if changes:
            message += "已更新字段:\n- " + "\n- ".join(changes)

        if verbose:
            message += f"\n\n详细信息:\n{json.dumps(workflow, ensure_ascii=False, indent=2)}"

        return True, message, workflow

    except Exception as e:
        logger.exception(f"更新工作流 '{workflow_id}' 时出错")
        return False, f"更新工作流时出错: {str(e)}", None
