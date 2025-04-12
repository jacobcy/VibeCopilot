#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行入口模块

提供命令行工具的主入口，处理命令行参数并调用对应的命令处理器。
"""

# 配置日志
import logging
import os
import sys
from typing import Dict, Type

import click
from rich.console import Console

from src.cli.command import Command
from src.cli.commands.db.db_click import db as db_click_group
from src.cli.commands.flow.flow_main import flow as flow_click_group
from src.cli.commands.help.help_click import help as help_command
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

# 命令映射
COMMANDS: Dict[str, Type[Command]] = {
    "status": status_command,
    "db": db_click_group,
    "help": help_command,
    "task": task_click_group,
}

# 命令分组
COMMAND_GROUPS = {"基础命令": ["status", "help"], "开发工具": ["rule", "flow", "task"], "数据管理": ["db", "memory"], "项目管理": ["roadmap", "template"]}


def create_cli_command(command_class: Type[Command]):
    """为命令类创建Click命令"""

    @click.command(help=command_class.__doc__ or "暂无帮助信息")
    @click.argument("args", nargs=-1)
    @friendly_error_handling
    def command_func(args):
        cmd = command_class()
        return cmd.execute(list(args))

    return command_func


def print_version(ctx, param, value):
    """打印版本信息"""
    if not value or ctx.resilient_parsing:
        return
    from src import __version__

    console.print(f"[bold]VibeCopilot[/bold] version: [bold blue]{__version__}[/bold blue]")
    ctx.exit()


def get_cli_app():
    """获取CLI应用实例"""

    @click.group(help="VibeCopilot CLI工具")
    @click.option("--version", is_flag=True, callback=print_version, expose_value=False, is_eager=True, help="显示版本信息")
    def cli():
        pass

    # 注册命令
    for cmd_name, cmd_class in COMMANDS.items():
        cli.add_command(create_cli_command(cmd_class), cmd_name)

    # 添加Click命令组
    cli.add_command(rule_click_group, name="rule")
    cli.add_command(roadmap_click_group, name="roadmap")
    cli.add_command(db_click_group, name="db")
    cli.add_command(flow_click_group, name="flow")
    cli.add_command(memory_click_group, name="memory")
    cli.add_command(template_command, name="template")
    cli.add_command(task_click_group, name="task")

    return cli


def print_error_message(command: str):
    """打印错误信息"""
    console.print(f"\n[bold red]错误:[/bold red] 未知命令: {command}")
    console.print("\n可用命令:")

    for group, commands in COMMAND_GROUPS.items():
        console.print(f"\n[bold]{group}[/bold]")
        for cmd in commands:
            if cmd in COMMANDS:
                cmd_class = COMMANDS[cmd]
                console.print(f"  {cmd:<10} {cmd_class.__doc__ or '暂无描述'}")


def main():
    """CLI主入口"""
    try:
        # 预准备数据库
        ensure_tables_exist(force_recreate=False)

        cli = get_cli_app()
        cli(standalone_mode=False)
    except click.exceptions.NoSuchOption as e:
        console.print(f"\n[bold red]错误:[/bold red] 无效的选项: {e.option_name}")
        console.print(f"使用 [bold]vibecopilot {e.ctx.command.name} --help[/bold] 查看有效的选项")
    except click.exceptions.UsageError as e:
        if "No such command" in str(e):
            command = str(e).split('"')[1]
            print_error_message(command)
        else:
            console.print(f"\n[bold red]错误:[/bold red] {str(e)}")
    except Exception as e:
        logger.exception("命令执行出错")
        console.print(f"\n[bold red]错误:[/bold red] {str(e)}")
    sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
