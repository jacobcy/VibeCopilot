#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库命令模块 - Click实现

提供知识库命令的实现，支持内容存储、检索和管理。
"""

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
    handle_show_subcommand,
    handle_sync_subcommand,
    handle_update_subcommand,
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
@click.option("--path", required=True, help="文档路径或标识符")
@click.option("--format", type=click.Choice(["json", "text"]), default="text", help="输出格式")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def show(path, format, verbose, agent_mode):
    """显示知识库内容详情"""
    args = click.get_current_context().params
    success, message, data = handle_show_subcommand(args)
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
@click.option("--path", required=True, help="文档路径或标识符")
@click.option("--force", is_flag=True, help="强制删除，不提示确认")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def delete(path, force, verbose, agent_mode):
    """删除知识库内容"""
    args = click.get_current_context().params
    success, message, data = handle_delete_subcommand(args)
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
@click.option("--source-dir", required=True, help="源文档目录")
@click.option("--recursive", is_flag=True, help="递归导入子目录")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def import_docs(source_dir, recursive, verbose, agent_mode):
    """导入本地文档到知识库"""
    args = click.get_current_context().params
    success, message, data = handle_import_subcommand(args)
    if success:
        click.echo(message)
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


@memory.command()
@click.option("--sync-type", required=True, type=click.Choice(["to-obsidian", "to-docs", "watch"]), help="同步类型")
@click.option("--verbose", "-v", is_flag=True, help="提供详细输出")
@click.option("--agent-mode", is_flag=True, help="启用agent优化的输出格式")
def sync(sync_type, verbose, agent_mode):
    """同步Obsidian和标准文档"""
    args = click.get_current_context().params
    success, message, data = handle_sync_subcommand(args)
    if success:
        click.echo(message)
    else:
        click.echo(f"错误: {message}", err=True)
