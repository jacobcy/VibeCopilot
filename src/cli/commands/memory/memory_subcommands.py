#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库子命令处理模块

提供知识库命令的子命令处理函数。
"""

import argparse
import logging
from typing import Any, Dict, List, Tuple

from src.cli.commands.memory.handlers import (
    handle_export,
    handle_import,
    handle_read_note,
    handle_search_notes,
    handle_sync,
    handle_write_note,
)

logger = logging.getLogger(__name__)


def handle_write_subcommand(args: argparse.Namespace) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理写入子命令

    Args:
        args: 解析后的参数对象

    Returns:
        元组，包含(是否成功, 消息, 附加数据)
    """
    # 检查必需参数
    if not args.title:
        return False, "错误: 缺少必要参数 --title (文档标题)", {}

    if not args.folder:
        return False, "错误: 缺少必要参数 --folder (存储目录)", {}

    # 获取内容
    # 在实际实现中，这里可能需要从当前会话或剪贴板获取内容
    content = args.content or "这是示例内容。实际实现中将使用会话内容或用户提供的内容。"

    # 调用处理函数
    return handle_write_note(content=content, title=args.title, folder=args.folder, tags=args.tags)


def handle_read_subcommand(args: argparse.Namespace) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理读取子命令

    Args:
        args: 解析后的参数对象

    Returns:
        元组，包含(是否成功, 消息, 附加数据)
    """
    # 检查必需参数
    if not args.path:
        return False, "错误: 缺少必要参数 --path (文档路径或标识符)", {}

    # 调用处理函数
    return handle_read_note(path=args.path)


def handle_search_subcommand(args: argparse.Namespace) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    处理搜索子命令

    Args:
        args: 解析后的参数对象

    Returns:
        元组，包含(是否成功, 消息, 结果列表)
    """
    # 检查必需参数
    if not args.query:
        return False, "错误: 缺少必要参数 --query (搜索关键词)", []

    # 调用处理函数
    return handle_search_notes(query=args.query, content_type=args.type)


def handle_import_subcommand(args: argparse.Namespace) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理导入子命令

    Args:
        args: 解析后的参数对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 检查必需参数
    if not args.source_dir:
        return False, "错误: 缺少必要参数 source_dir (源文档目录)", {}

    # 调用处理函数
    return handle_import(source_dir=args.source_dir)


def handle_export_subcommand(args: argparse.Namespace) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理导出子命令

    Args:
        args: 解析后的参数对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 调用处理函数
    return handle_export(db_path=args.db, output_dir=args.output)


def handle_sync_subcommand(args: argparse.Namespace) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理同步子命令

    Args:
        args: 解析后的参数对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 调用处理函数
    return handle_sync(sync_type=args.sync_type)
