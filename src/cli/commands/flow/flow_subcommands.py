#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流子命令处理模块

提供工作流命令的各种子命令处理函数
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.cli.commands.flow.handlers import (
    handle_create_workflow,
    handle_export_workflow,
    handle_flow_type,
    handle_get_workflow_context,
    handle_list_workflows,
    handle_view_workflow,
)

logger = logging.getLogger(__name__)


def handle_list_subcommand(args: Any) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
    """
    处理list子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    return handle_list_workflows()


def handle_create_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理create子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.rule_path:
        return False, "缺少必要的规则文件路径", None

    return handle_create_workflow(args.rule_path)


def handle_view_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理view子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.workflow_id:
        return False, "缺少必要的工作流ID", None

    return handle_view_workflow(args.workflow_id)


def handle_context_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理context子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.workflow_id:
        return False, "缺少必要的工作流ID", None

    return handle_get_workflow_context(args.workflow_id)


def handle_export_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理export子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.workflow_id:
        return False, "缺少必要的工作流ID", None

    format_type = args.format or "json"
    return handle_export_workflow(args.workflow_id, format_type)


def handle_flow_type_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理flow_type子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.flow_type:
        return False, "缺少必要的流程类型", None

    return handle_flow_type(args.flow_type)
