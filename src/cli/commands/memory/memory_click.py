#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库命令模块 - Click实现

提供知识库命令的实现，支持内容存储、检索和管理。
"""

import os

import click
from rich.console import Console
from rich.table import Table

from src.cli.commands.memory.memory_subcommands import (
    handle_create_subcommand,
    handle_delete_subcommand,
    handle_export_subcommand,
    handle_import_subcommand,
    handle_list_subcommand,
    handle_search_subcommand,
    handle_update_subcommand,
    handle_watch_subcommand,
    show_memory_cli,
)

console = Console()


@click.group()
def memory():
    """管理VibeCopilot知识库，支持内容存储、检索和管理"""
    pass


@memory.command()
@click.option("--folder", help="筛选特定目录的内容")
@click.option("--format", type=click.Choice(["json", "text"]), default="text", help="输出格式")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def list(folder, format, verbose, agent_mode):
    """列出知识库内容"""
    args = click.get_current_context().params
    success, message, data = handle_list_subcommand(args)
    if success:
        click.echo(message)
        if verbose and data:
            click.echo("\n详细信息:")
            for idx, item in enumerate(data, 1):
                click.echo(f"[{idx}] {item}")
    else:
        click.echo(f"错误: {message}", err=True)


@memory.command()
@click.argument("path", required=False)
@click.option("--path", "path_option", help="内存项路径，例如 memory:///readme 或 folder/title")
@click.option("--format", type=click.Choice(["json", "text"]), default="text", help="输出格式")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def show(path, path_option, format, verbose, agent_mode):
    """显示知识库内容详情

    可以通过位置参数或--path选项指定路径
    例如:
      vibecopilot memory show folder/title
      vibecopilot memory show --path folder/title
    """
    # 优先使用位置参数，如果没有则使用--path选项
    actual_path = path if path else path_option

    if not actual_path:
        click.echo("错误: 必须提供path参数或--path选项", err=True)
        return

    args = {"path": actual_path, "format": format, "verbose": verbose, "agent_mode": agent_mode}
    success, message, data = show_memory_cli(args)
    if success:
        click.echo(message)
        if verbose and data:
            click.echo("\n详细信息:")
            click.echo(data)
    else:
        click.echo(f"错误: {message}", err=True)


@memory.command()
@click.option("--title", required=True, help="文档标题")
@click.option("--folder", required=True, help="存储目录")
@click.option("--tags", help="标签列表，逗号分隔")
@click.option("--content", help="要保存的内容（如果不提供，将使用当前对话内容）")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def create(title, folder, tags, content, verbose, agent_mode):
    """创建知识库内容"""
    args = click.get_current_context().params
    success, message, data = handle_create_subcommand(args)
    if success:
        click.echo(message)
    else:
        click.echo(f"错误: {message}", err=True)


@memory.command()
@click.option("--path", required=True, help="文档路径或标识符")
@click.option("--content", required=True, help="更新后的内容")
@click.option("--tags", help="更新的标签，逗号分隔")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def update(path, content, tags, verbose, agent_mode):
    """更新知识库内容"""
    args = click.get_current_context().params
    success, message, data = handle_update_subcommand(args)
    if success:
        click.echo(message)
    else:
        click.echo(f"错误: {message}", err=True)


@memory.command()
@click.argument("path", required=True)
@click.option("--force", is_flag=True, help="强制删除，不提示确认")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def delete(path, force, verbose, agent_mode):
    """删除知识库内容"""
    from src.memory import get_memory_service

    memory_service = get_memory_service()
    if verbose:
        click.echo(f"正在删除: {path} (强制: {force})")
    success, message, data = memory_service.delete_note(path, force)
    if success:
        click.echo(message)
    else:
        click.echo(f"错误: {message}", err=True)


@memory.command()
@click.option("--query", required=True, help="搜索关键词")
@click.option("--type", help="内容类型")
@click.option("--format", type=click.Choice(["json", "text"]), default="text", help="输出格式")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def search(query, type, format, verbose, agent_mode):
    """语义搜索知识库"""
    args = click.get_current_context().params
    success, message, data = handle_search_subcommand(args)
    if success:
        click.echo(message)
        if verbose and data:
            click.echo("\n搜索结果:")
            for idx, item in enumerate(data, 1):
                click.echo(f"[{idx}] {item}")
    else:
        click.echo(f"错误: {message}", err=True)


@memory.command()
@click.option("--db", help="数据库路径")
@click.option("--output", help="Obsidian输出目录")
@click.option("--format", type=click.Choice(["md", "json"]), default="md", help="导出格式")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def export(db, output, format, verbose, agent_mode):
    """导出知识库到Obsidian"""
    args = click.get_current_context().params
    success, message, data = handle_export_subcommand(args)
    if success:
        click.echo(message)
    else:
        click.echo(f"错误: {message}", err=True)


@memory.command(name="import")
@click.argument("source_path", required=False)
@click.option("--source", "-s", help="源文件或目录路径")
@click.option("--recursive", "-r", is_flag=True, help="递归导入子目录（仅当source为目录时有效）")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def import_cmd(source_path, source, recursive, verbose, agent_mode):
    """从外部导入文档到知识库，支持单个文件或目录"""
    args = click.get_current_context().params

    # 优先使用位置参数，如果没有则使用--source选项
    if source_path:
        args["source"] = source_path
    elif not source:
        click.echo("错误: 请提供要导入的文件或目录路径", err=True)
        return

    success, message, data = handle_import_subcommand(args)
    if success:
        # 如果是单个文件导入成功且有permalink，确保显示
        source_path = args.get("source")
        if "permalink" in data and source_path and not os.path.isdir(source_path):
            # 如果消息中已经包含permalink，直接输出
            if "永久链接" in message:
                click.echo(message)
            else:
                # 否则添加permalink到消息中
                click.echo(f"{message}\n永久链接: {data['permalink']}")
        else:
            click.echo(message)
    else:
        click.echo(f"错误: {message}", err=True)


@memory.command()
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def watch(verbose, agent_mode):
    """持续监控知识库文件变化并自动同步"""
    args = click.get_current_context().params
    success, message, data = handle_watch_subcommand(args)
    if success:
        click.echo(message)
    else:
        click.echo(f"错误: {message}", err=True)
