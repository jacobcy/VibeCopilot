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
    handle_get_workflow_context,
    handle_import_workflow,
    handle_list_workflows,
    handle_next_stage,
    handle_run_workflow_stage,
    handle_session_command,
    handle_show_workflow,
    handle_update_workflow,
    handle_visualize_workflow,
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
    workflow_type = getattr(args, "workflow_type", None)
    verbose = getattr(args, "verbose", False)
    return handle_list_workflows(workflow_type=workflow_type, verbose=verbose)


def handle_create_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理create子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.workflow_type:
        return False, "缺少必要的工作流类型参数", None

    name = getattr(args, "name", None)
    description = getattr(args, "description", None)
    verbose = getattr(args, "verbose", False)

    return handle_create_workflow(
        args.workflow_type, name=name, description=description, verbose=verbose
    )


def handle_update_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理update子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.id:
        return False, "缺少必要的工作流ID", None

    name = getattr(args, "name", None)
    description = getattr(args, "description", None)
    verbose = getattr(args, "verbose", False)

    return handle_update_workflow(args.id, name=name, description=description, verbose=verbose)


def handle_show_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理show子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.id:
        return False, "缺少必要的工作流ID", None

    format_type = getattr(args, "format", "text")
    verbose = getattr(args, "verbose", False)

    return handle_show_workflow(args.id, format_type=format_type, verbose=verbose)


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

    if not args.stage_id:
        return False, "缺少必要的阶段ID", None

    session_id = getattr(args, "session", None)
    completed = getattr(args, "completed", None)
    format_type = getattr(args, "format", "text")
    verbose = getattr(args, "verbose", False)

    return handle_get_workflow_context(
        args.workflow_id,
        stage_id=args.stage_id,
        session_id=session_id,
        completed_items=completed,
        format_type=format_type,
        verbose=verbose,
    )


def handle_next_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理next子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.session_id:
        return False, "缺少必要的会话ID", None

    current_stage = getattr(args, "current", None)
    format_type = getattr(args, "format", "text")
    verbose = getattr(args, "verbose", False)

    return handle_next_stage(
        args.session_id,
        current_stage_instance_id=current_stage,
        format_type=format_type,
        verbose=verbose,
    )


def handle_visualize_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理visualize子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.id:
        return False, "缺少必要的ID参数", None

    is_session = getattr(args, "session", False)
    format_type = getattr(args, "format", "mermaid")
    output_path = getattr(args, "output", None)
    verbose = getattr(args, "verbose", False)

    return handle_visualize_workflow(
        args.id,
        is_session=is_session,
        format_type=format_type,
        output_path=output_path,
        verbose=verbose,
    )


def handle_export_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理export子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.id:
        return False, "缺少必要的工作流ID", None

    format_type = getattr(args, "format", "json")
    output_path = getattr(args, "output", None)
    verbose = getattr(args, "verbose", False)

    return handle_export_workflow(
        args.id, format_type=format_type, output_path=output_path, verbose=verbose
    )


def handle_import_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理import子命令

    Args:
        args: 命令行参数

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.file_path:
        return False, "缺少必要的文件路径", None

    overwrite = getattr(args, "overwrite", False)
    verbose = getattr(args, "verbose", False)

    return handle_import_workflow(args.file_path, overwrite=overwrite, verbose=verbose)


def handle_run_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理run子命令，支持workflow_name:stage_name格式

    Args:
        args: 命令行参数，包含workflow_stage（格式为workflow_name:stage_name）

    Returns:
        包含状态、消息和数据的元组
    """
    if not args.workflow_stage:
        return False, "缺少必要的工作流和阶段参数 (格式应为 workflow_name:stage_name)", None

    # 解析工作流和阶段名称
    parts = args.workflow_stage.split(":")
    if len(parts) != 2:
        return False, f"无效的工作流阶段格式: {args.workflow_stage}, 应为 workflow_name:stage_name", None

    workflow_name, stage_name = parts

    # 准备参数
    params = {
        "workflow_name": workflow_name,
        "stage_name": stage_name,
        "name": getattr(args, "name", None),
        "completed": getattr(args, "completed", None),
        "session_id": getattr(args, "session", None),
        "verbose": getattr(args, "verbose", False),
    }

    return handle_run_workflow_stage(params)


def handle_session_subcommand(args: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理session子命令

    Args:
        args: 命令行参数，包含action和其他会话相关参数

    Returns:
        包含状态、消息和数据的元组
    """
    return handle_session_command(args)
