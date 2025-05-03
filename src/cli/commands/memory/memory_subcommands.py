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
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果列表)
    """
    # 使用统一的MemoryService
    return _memory_service.list_notes(folder=_get_attr(args, "folder"))


@click.command(name="show", help="显示内存项内容")
@click.argument("path", required=True)  # 移除 help 参数，或确保它在命令级别定义
def show_memory_cli(path: str) -> None:
    """
    显示指定内存项的内容。路径示例：memory:///readme
    """
    try:
        # 使用 path 参数直接获取并显示内容
        memory_service = MemoryService()  # 假设服务实例化
        item = memory_service.get_item_by_path(path)  # 替换为实际方法
        if item:
            console.print(f"内容: {item.content}")  # 简化输出，替换为实际逻辑
        else:
            console.print("[yellow]未找到指定内存项[/yellow]")
    except Exception as e:
        console.print(f"[red]显示内存项失败: {str(e)}[/red]")
        logger.error(f"显示内存项出错: {e}")


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
    # 修复：确认在有管道输入时能正确处理
    content = _get_attr(args, "content")

    # 如果没有提供content，尝试从标准输入读取
    if not content and not sys.stdin.isatty():
        content = sys.stdin.read()

    # 仍然没有内容时使用默认值
    if not content:
        content = "这是示例内容。实际实现中将使用会话内容或用户提供的内容。"

    # 使用统一的MemoryService
    return _memory_service.create_note(content=content, title=title, folder=folder, tags=_get_attr(args, "tags"))


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

    # 使用统一的MemoryService
    return _memory_service.update_note(path=path, content=content, tags=_get_attr(args, "tags"))


@click.command()
@click.argument("path", required=True)  # 确保 path 作为位置参数
@click.option("-f", "--force", is_flag=True, help="强制删除，不提示确认")
@click.option("-v", "--verbose", is_flag=True, help="提供详细输出")
def handle_delete_subcommand(path: str, force: bool, verbose: bool) -> None:
    """
    处理删除知识库内容

    Args:
        path: 文档路径或标识符（位置参数）
        force: 是否强制删除
        verbose: 是否显示详细输出
    """
    if verbose:
        click.echo(f"正在删除: {path} (强制: {force})")
    success, message, data = _memory_service.delete_note(path, force)
    click.echo(message)
    if verbose and success:
        click.echo(f"操作详情: {data}")


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

    # 使用统一的MemoryService
    return _memory_service.search_notes(query=query, content_type=_get_attr(args, "type"))


def handle_import_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理导入子命令

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 获取源路径参数（可能来自位置参数或选项）
    source = _get_attr(args, "source")

    # 在memory_click.py中已经处理了source为空的情况，这里是额外的检查
    if not source:
        return False, "错误: 请提供要导入的文件或目录路径", {}

    # 使用统一的MemoryService
    recursive = _get_attr(args, "recursive", False)
    return _memory_service.import_documents(source_path=source, recursive=recursive)


def handle_export_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理导出子命令

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 获取参数
    output_dir = _get_attr(args, "output")
    format_type = _get_attr(args, "format", "md")

    # 使用统一的MemoryService
    return _memory_service.export_documents(output_dir=output_dir, format_type=format_type)


def handle_sync_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理同步子命令

    只同步docs/目录下的文档，不同步规则
    注意：仅此命令使用同步编排器而非MemoryService

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    try:
        # 导入SyncOrchestrator，避免直接依赖memory内部实现
        import asyncio

        from src.status.sync.sync_orchestrator import SyncOrchestrator

        # 创建SyncOrchestrator实例
        sync_orchestrator = SyncOrchestrator()

        # 仅同步document类型，不同步规则
        coroutine = sync_orchestrator.sync_by_type("document")

        # 使用事件循环执行异步函数
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # 如果没有可用的事件循环，创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(coroutine)

        # 处理结果
        total_synced = result.get("total_synced", 0)
        return True, f"文档同步完成：已同步{total_synced}个文档", result
    except ImportError as e:
        # 如果无法导入SyncOrchestrator，报错
        logger.error(f"无法导入同步编排器: {e}")
        return False, "文档同步失败：无法导入同步编排器", {"error": str(e)}
    except Exception as e:
        # 捕获所有其他异常
        logger.error(f"文档同步失败: {e}")
        return False, f"文档同步失败: {str(e)}", {"error": str(e)}


def handle_watch_subcommand(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理监控子命令，启动知识库内容变更监控

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 使用统一的MemoryService
    return _memory_service.start_sync_watch()


def show_memory_cli(args: Union[Dict[str, Any], Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    处理show子命令，显示知识库内容详情

    Args:
        args: 命令行参数，可以是字典或任何支持getattr的对象

    Returns:
        元组，包含(是否成功, 消息, 结果数据)
    """
    # 检查必需参数
    path = _get_attr(args, "path")
    if not path:
        return False, "错误: 缺少必要参数 path (内存项路径)", {}

    # 使用统一的MemoryService
    # 这里应该是调用真实的memory_service.read_note或类似方法
    try:
        # 实际的服务调用
        return _memory_service.read_note(path=path)
    except Exception as e:
        logger.error(f"显示内存项出错: {e}")
        return False, f"显示内存项失败: {str(e)}", {}
