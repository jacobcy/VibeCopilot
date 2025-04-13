#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行入口模块

提供命令行工具的主入口，处理命令行参数并调用对应的命令处理器。
"""

import logging
import os
import sys

import click
from rich.console import Console

from src.cli.commands.db.db_click import db as db_click_group
from src.cli.commands.flow.flow_main import flow as flow_click_group
from src.cli.commands.memory.memory_click import memory as memory_click_group
from src.cli.commands.roadmap.roadmap_click import roadmap as roadmap_click_group
from src.cli.commands.rule.rule_click import rule as rule_click_group
from src.cli.commands.status.status_click import status as status_command
from src.cli.commands.task.task_click import task as task_click_group
from src.cli.commands.template.template_click import template as template_command
from src.cli.decorators import friendly_error_handling

# 预初始化数据库连接管理器
from src.db.connection_manager import ensure_tables_exist

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)
console = Console()

# 命令分组（用于帮助显示）
COMMAND_GROUPS = {"基础命令": ["status"], "开发工具": ["rule", "flow", "template"], "数据管理": ["db", "memory"], "项目管理": ["roadmap", "task"]}


def print_version(ctx, param, value):
    """打印版本信息"""
    if not value or ctx.resilient_parsing:
        return
    from src import __version__

    console.print(f"[bold]VibeCopilot[/bold] version: [bold blue]{__version__}[/bold blue]")
    ctx.exit()


def get_cli_app():
    """获取CLI应用实例"""

    @click.group(help="VibeCopilot CLI工具", context_settings={"help_option_names": ["-h", "--help"]})
    @click.option("--version", is_flag=True, callback=print_version, expose_value=False, is_eager=True, help="显示版本信息")
    def cli():
        """VibeCopilot 命令行工具

        使用 --help 选项查看可用命令和选项
        """
        pass

    # 使用 Click 方式注册所有命令
    cli.add_command(status_command)
    cli.add_command(rule_click_group)
    cli.add_command(roadmap_click_group)
    cli.add_command(db_click_group)
    cli.add_command(flow_click_group)
    cli.add_command(memory_click_group)
    cli.add_command(template_command)
    cli.add_command(task_click_group)

    return cli


def print_error_message(command: str):
    """打印错误信息"""
    console.print(f"\n[bold red]错误:[/bold red] 未知命令: {command}")
    console.print("\n可用命令:")

    for group, commands in COMMAND_GROUPS.items():
        console.print(f"\n[bold]{group}[/bold]")
        for cmd in commands:
            console.print(f"  {cmd}")

    console.print("\n使用 [bold]vibecopilot --help[/bold] 查看详细帮助信息")


def main():
    """CLI主入口"""
    try:
        # 预准备数据库
        ensure_tables_exist(force_recreate=False)

        # 执行CLI命令
        cli = get_cli_app()
        cli()
        return 0  # 成功执行返回 0
    except click.exceptions.NoSuchOption as e:
        console.print(f"\n[bold red]错误:[/bold red] 无效的选项: {e.option_name}")
        console.print(f"使用 [bold]vibecopilot {e.ctx.command.name} --help[/bold] 查看有效的选项")
        return 1
    except click.exceptions.UsageError as e:
        if "No such command" in str(e):
            command = str(e).split('"')[1]
            print_error_message(command)
        else:
            console.print(f"\n[bold red]错误:[/bold red] {str(e)}")
        return 1
    except Exception as e:
        logger.exception("命令执行出错")
        console.print(f"\n[bold red]错误:[/bold red] {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
