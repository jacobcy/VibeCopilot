#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库子命令处理模块

提供知识库命令的子命令处理函数。
"""

import logging
import sys
from typing import Any, Dict, List, Tuple, Union

import click  # 确保导入 click 或相关库

from src.memory import MemoryService, get_memory_service

logger = logging.getLogger(__name__)

# 创建MemoryService的单例，所有处理函数共享使用
_memory_service = get_memory_service()


def _get_attr(args: Union[Dict[str, Any], Any], name: str, default=None) -> Any:
    """从参数对象获取属性值，支持字典和Namespace对象"""
    if isinstance(args, dict):
        return args.get(name, default)
    return getattr(args, name, default)


def handle_list_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    处理列表子命令，列出知识库内容

    Args:
        args: 命令行参数，字典格式

    Returns:
        元组，包含(是否成功, 消息, 结果列表)
    """
    # 使用统一的MemoryService
    # 假设 MemoryService.list_notes 返回正确的元组格式
    return _memory_service.list_notes(folder=_get_attr(args, "folder"))


def show_memory_cli(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理show子命令，显示知识库内容详情

    Args:
        args: 命令行参数，字典格式

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 检查必需参数
    path = _get_attr(args, "path")
    if not path:
        return False, "错误: 缺少必要参数 path (内存项路径)", {}

    # 使用统一的MemoryService
    try:
        # 假设 MemoryService.read_note 返回正确的元组格式
        return _memory_service.read_note(path_or_permalink=path)
    except Exception as e:
        logger.error(f"显示内存项出错: {e}")
        return False, f"显示内存项失败: {str(e)}", {}


def handle_create_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理创建子命令 (原write子命令)

    Args:
        args: 命令行参数，字典格式

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
    content = _get_attr(args, "content")

    # 如果没有提供content，尝试从标准输入读取
    if not content and not sys.stdin.isatty():
        content = sys.stdin.read()

    # 仍然没有内容时使用默认值 (或者可以报错)
    if not content:
        # 考虑是否应该报错而不是使用默认值
        # return False, "错误: 缺少内容", {}
        content = "这是示例内容。实际实现中将使用会话内容或用户提供的内容。"  # 临时保留

    # 使用统一的MemoryService
    # 假设 MemoryService.create_note 返回正确的元组格式
    return _memory_service.create_note(content=content, title=title, folder=folder, tags=_get_attr(args, "tags"))


def handle_update_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理更新子命令，更新知识库内容

    Args:
        args: 命令行参数，字典格式

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 检查必需参数
    path = _get_attr(args, "path")
    if not path:
        return False, "错误: 缺少必要参数 --path (文档路径或标识符)", {}

    content = _get_attr(args, "content")
    # 更新时内容是否必须？取决于设计，这里假设是必须的
    if not content:
        return False, "错误: 缺少必要参数 --content (更新后的内容)", {}

    # 使用统一的MemoryService
    # 假设 MemoryService.update_note 返回正确的元组格式
    return _memory_service.update_note(path=path, content=content, tags=_get_attr(args, "tags"))


def handle_delete_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理删除知识库内容

    Args:
        args: 命令行参数，字典格式

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    path = _get_attr(args, "path")
    if not path:
        return False, "错误: 缺少必要参数 path (文档路径或标识符)", {}

    force = _get_attr(args, "force", False)
    # verbose 参数现在由 Click 在 memory_click.py 中处理，子命令只负责核心逻辑
    # verbose = _get_attr(args, "verbose", False)
    # if verbose:
    #     click.echo(f"正在删除: {path} (强制: {force})") # 输出逻辑移到 memory_click.py

    # 使用统一的MemoryService
    # 假设 MemoryService.delete_note 返回正确的元组格式
    # 注意：MemoryService.delete_note 需要能处理 identifier_or_permalink
    return _memory_service.delete_note(path_or_permalink=path, force=force)


def handle_search_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    处理搜索子命令

    Args:
        args: 命令行参数，字典格式

    Returns:
        元组，包含(是否成功, 消息, 结果列表)
    """
    # 检查必需参数
    query = _get_attr(args, "query")
    if not query:
        return False, "错误: 缺少必要参数 --query (搜索关键词)", []

    # 使用统一的MemoryService
    # 假设 MemoryService.search_notes 返回正确的元组格式
    return _memory_service.search_notes(query=query, content_type=_get_attr(args, "type"))


def handle_import_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理导入子命令

    Args:
        args: 命令行参数，字典格式

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 获取源路径参数
    source = _get_attr(args, "source")  # 已在 memory_click.py 中处理了位置参数和 --source

    if not source:
        # 这个检查理论上不应该触发，因为 memory_click.py 做了检查
        return False, "错误: 请提供要导入的文件或目录路径", {}

    # 使用统一的MemoryService
    recursive = _get_attr(args, "recursive", False)
    # 假设 MemoryService.import_documents 返回正确的元组格式
    return _memory_service.import_documents(source_path=source, recursive=recursive)


def handle_export_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理导出子命令

    Args:
        args: 命令行参数，字典格式

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 获取参数
    output_dir = _get_attr(args, "output")
    format_type = _get_attr(args, "format", "md")

    # 使用统一的MemoryService
    # 假设 MemoryService.export_documents 返回正确的元组格式
    return _memory_service.export_documents(output_dir=output_dir, format_type=format_type)


def handle_watch_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理监控子命令，启动知识库内容变更监控

    Args:
        args: 命令行参数，字典格式

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 使用统一的MemoryService
    # 假设 MemoryService.start_sync_watch 返回正确的元组格式
    return _memory_service.start_sync_watch()
