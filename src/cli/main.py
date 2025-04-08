#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行入口模块

提供命令行工具的主入口，处理命令行参数并调用对应的命令处理器。
"""

import os
import sys

from dotenv import load_dotenv

# 确保在任何其他导入之前加载环境变量
load_dotenv(override=True)

# 确保src目录在Python路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import importlib
import logging
from typing import Dict, Type, Union

import click
import typer
from typer.main import get_command

from src.cli.command import Command
from src.cli.command_parser import CommandParser
from src.cli.commands.db import DatabaseCommand
from src.cli.commands.db.db_click import db as db_click_group
from src.cli.commands.flow.flow_click import flow as flow_click_group
from src.cli.commands.help.help_command import HelpCommand  # Keep for now, might refactor later
from src.cli.commands.memory.memory_click import memory as memory_click_group
from src.cli.commands.roadmap.roadmap_click import roadmap as roadmap_click_group
from src.cli.commands.rule.rule_click import rule as rule_click_group
from src.cli.commands.status import StatusCommand  # Keep for now, might refactor later
from src.cli.commands.task import task_app
from src.cli.commands.template.template_command import TemplateCommand  # Keep for now, might refactor later

# 预初始化数据库连接管理器
from src.db.connection_manager import ensure_tables_exist

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# 命令映射
# Note: Typer app 'task' is handled specially in get_cli_app
# Remove 'rule', 'flow' and 'memory' from this dict as they're now handled directly as click groups
COMMANDS: Dict[str, Type[Command]] = {
    "status": StatusCommand,  # Keep for now
    "db": DatabaseCommand,
    "help": HelpCommand,
    "template": TemplateCommand,
}


def create_cli_command(command_class: Type[Command]):
    """为命令类创建Click命令"""

    @click.command(help=command_class.get_help())
    @click.argument("args", nargs=-1)
    def command_func(args):
        cmd = command_class()
        return cmd.execute(list(args))

    return command_func


def get_cli_app():
    """
    获取CLI应用实例
    用于测试和其他需要访问CLI的场景
    """

    @click.group(help="VibeCopilot CLI工具")
    def cli():
        pass

    # Register remaining old-style commands (to be refactored later)
    for cmd_name, cmd_class in COMMANDS.items():
        cli.add_command(create_cli_command(cmd_class), cmd_name)

    # Add the new click-based command groups
    cli.add_command(rule_click_group, name="rule")
    cli.add_command(roadmap_click_group, name="roadmap")
    cli.add_command(db_click_group, name="db")
    cli.add_command(flow_click_group, name="flow")
    cli.add_command(memory_click_group, name="memory")

    # Add the Typer app task_app (already converted to Click command)
    # 将 Typer 应用转换为 Click 命令并添加
    cli.add_command(get_command(task_app), name="task")

    return cli


def main():
    """
    CLI主入口
    """
    # 预准备数据库，仅确保表存在，不进行重建
    ensure_tables_exist(force_recreate=False)

    cli = get_cli_app()
    return cli()


def print_help():
    """打印帮助信息"""
    print("VibeCopilot CLI工具")
    print("\n可用命令:")
    # Print help for remaining old-style commands
    for cmd_name, cmd_class in COMMANDS.items():
        if issubclass(cmd_class, Command):
            print(f"  {cmd_name:<10} {cmd_class.get_help()}")  # Keep old help format for these for now

    # Click automatically handles help for added groups/commands
    print(f"  {'rule':<10} 规则管理命令 (使用 'vc rule --help' 查看子命令)")
    print(f"  {'flow':<10} 工作流管理命令 (使用 'vc flow --help' 查看子命令)")
    print(f"  {'task':<10} 任务管理命令 (使用 'vc task --help' 查看子命令)")
    print(f"  {'roadmap':<10} 路线图管理命令 (使用 'vc roadmap --help' 查看子命令)")
    print(f"  {'db':<10} 数据库管理命令 (使用 'vc db --help' 查看子命令)")
    print(f"  {'memory':<10} 知识库管理命令 (使用 'vc memory --help' 查看子命令)")

    print("\n用法:")
    print("  vibecopilot <命令> [参数]")
    print("  vibecopilot help [命令]")
    print("  vibecopilot roadmap story S1")
    print("  vibecopilot rule list")
    print("  vibecopilot flow test")
    print("  vibecopilot status show")
    print("  vibecopilot db init")


if __name__ == "__main__":
    sys.exit(main())
