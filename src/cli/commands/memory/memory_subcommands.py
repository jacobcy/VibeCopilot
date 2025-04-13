#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库子命令处理模块

提供知识库命令的子命令处理函数。
"""

import logging
from typing import Any, Dict, List, Tuple, Union

from src.cli.commands.memory.handlers import (
    handle_delete_note,
    handle_export,
    handle_import,
    handle_list_notes,
    handle_read_note,
    handle_search_notes,
    handle_sync,
    handle_update_note,
    handle_write_note,
)

logger = logging.getLogger(__name__)


def _get_attr(args: Union[Dict[str, Any], Any], name: str, default=None) -> Any:
    """从参数对象获取属性值，支持字典和Namespace对象"""
    if isinstance(args, dict):
        return args.get(name, default)
    return getattr(args, name, default)


def handle_list_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    处理列表子命令，列出知识库内容

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果列表)
    """
    # 调用处理函数
    return handle_list_notes(folder=_get_attr(args, "folder"))


def handle_show_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理显示子命令，显示知识库内容详情

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 检查必需参数
    path = _get_attr(args, "path")
    if not path:
        return False, "错误: 缺少必要参数 --path (文档路径或标识符)", {}

    # 调用处理函数
    return handle_read_note(path=path)


def handle_create_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理创建子命令 (原write子命令)

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 附加数据)
    """
    # 检查必需参数
    title = _get_attr(args, "title")
    if not title:
        return False, "错误: 缺少必要参数 --title (文档标题)", {}

    folder = _get_attr(args, "folder")
    if not folder:
        return False, "错误: 缺少必要参数 --folder (存储目录)", {}

    # 获取内容
    # 在实际实现中，这里可能需要从当前会话或剪贴板获取内容
    content = _get_attr(args, "content") or "这是示例内容。实际实现中将使用会话内容或用户提供的内容。"

    # 调用处理函数
    return handle_write_note(content=content, title=title, folder=folder, tags=_get_attr(args, "tags"))


def handle_update_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理更新子命令，更新知识库内容

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 检查必需参数
    path = _get_attr(args, "path")
    if not path:
        return False, "错误: 缺少必要参数 --path (文档路径或标识符)", {}

    content = _get_attr(args, "content")
    if not content:
        return False, "错误: 缺少必要参数 --content (更新后的内容)", {}

    # 调用处理函数
    return handle_update_note(path=path, content=content, tags=_get_attr(args, "tags"))


def handle_delete_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理删除子命令，删除知识库内容

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 检查必需参数
    path = _get_attr(args, "path")
    if not path:
        return False, "错误: 缺少必要参数 --path (文档路径或标识符)", {}

    # 调用处理函数
    force = _get_attr(args, "force", False)
    return handle_delete_note(path=path, force=force)


def handle_search_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    处理搜索子命令

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果列表)
    """
    # 检查必需参数
    query = _get_attr(args, "query")
    if not query:
        return False, "错误: 缺少必要参数 --query (搜索关键词)", []

    # 调用处理函数
    return handle_search_notes(query=query, content_type=_get_attr(args, "type"))


def handle_import_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理导入子命令

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 检查必需参数
    source_dir = _get_attr(args, "source_dir")
    if not source_dir:
        return False, "错误: 缺少必要参数 --source-dir (源文档目录)", {}

    # 调用处理函数
    recursive = _get_attr(args, "recursive", False)
    return handle_import(source_dir=source_dir, recursive=recursive)


def handle_export_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理导出子命令

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 获取可选参数
    format_type = _get_attr(args, "format", "md")

    # 调用处理函数
    return handle_export(db_path=_get_attr(args, "db"), output_dir=_get_attr(args, "output"), format_type=format_type)


def handle_sync_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理同步子命令

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 检查必需参数
    sync_type = _get_attr(args, "sync_type")
    if not sync_type:
        return False, "错误: 缺少必要参数 --sync-type (同步类型)", {}

    # 调用处理函数
    return handle_sync(sync_type=sync_type)
