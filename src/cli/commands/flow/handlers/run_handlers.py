#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流运行处理模块

提供运行工作流特定阶段的功能
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from src.cli.commands.flow.handlers.create_handlers import handle_create_workflow
from src.cli.commands.flow.handlers.utils import (
    _find_workflow_rule_paths,
    _format_checklist,
    _format_deliverables,
    _save_stage_instance,
)
from src.workflow.config import PROJECT_ROOT
from src.workflow.interpreter.context_provider import ContextProvider
from src.workflow.template_loader import create_workflow_from_template, load_flow_template
from src.workflow.workflow_operations import get_workflow, get_workflow_by_name

logger = logging.getLogger(__name__)


def handle_run_workflow_stage(params: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理运行工作流特定阶段的请求

    参数格式为 workflow_name:stage_name，例如 dev:story 表示运行开发工作流的故事阶段

    Args:
        params: 包含以下参数的字典
            - workflow_name: 工作流名称
            - stage_name: 阶段名称
            - name: 阶段实例名称（可选）
            - completed: 已完成的项目列表（可选）
            - session_id: 会话ID（可选），如果提供则使用现有会话

    Returns:
        包含状态、消息和结果数据的元组
    """
    workflow_name = params.get("workflow_name")
    stage_name = params.get("stage_name")
    stage_instance_name = params.get("name", f"{workflow_name}-{stage_name}")
    completed_items = params.get("completed", [])
    session_id = params.get("session_id")

    if not workflow_name or not stage_name:
        return False, "缺少必要的工作流名称或阶段名称", None

    logger.info(f"处理工作流阶段执行请求: {workflow_name}:{stage_name}")

    # 使用flow_cmd.py中的run_workflow_stage函数，它已经实现了session集成
    from src.workflow.flow_cmd import run_workflow_stage

    # 调用集成了session的函数
    success, message, result = run_workflow_stage(
        workflow_name=workflow_name,
        stage_name=stage_name,
        instance_name=stage_instance_name,
        completed_items=completed_items,
        session_id=session_id,
    )

    # 如果执行成功，添加关于会话的额外说明
    if success and result:
        # 从结果中提取会话和阶段信息
        result_session_id = result.get("session_id", "未知")
        session_created = not session_id and result_session_id != "未知"
        stage_instance_id = result.get("stage_instance_id", "未知")

        # 根据是否创建了新会话添加不同的提示
        session_hint = "\n\n🔄 会话管理:"
        if session_created:
            session_hint += f"""
- 已创建新会话: {result_session_id}
- 查看会话详情: vc flow session show {result_session_id}
- 暂停此会话: vc flow session pause {result_session_id}
- 在此会话中继续执行: vc flow run <workflow>:<stage> --session={result_session_id}"""
        else:
            session_hint += f"""
- 使用会话: {result_session_id}
- 继续在此会话中执行其他阶段: vc flow run <workflow>:<stage> --session={result_session_id}
- 查看完整会话进度: vc flow session show {result_session_id}"""

        # 添加关于上下文的提示
        context_hint = f"""

📝 上下文管理:
- 当前状态和上下文已保存
- 如果中断操作，可随时恢复此会话继续工作"""

        # 合并原始消息和新的提示
        message = f"{message}{session_hint}{context_hint}"

    return success, message, result
