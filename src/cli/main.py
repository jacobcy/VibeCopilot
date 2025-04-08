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
from typing import Dict, Type

import click

from src.cli.command import Command
from src.cli.command_parser import CommandParser
from src.cli.commands.db import DatabaseCommand
from src.cli.commands.flow.flow_command import FlowCommand
from src.cli.commands.help.help_command import HelpCommand
from src.cli.commands.memory import MemoryCommand
from src.cli.commands.roadmap.roadmap_command import RoadmapCommand
from src.cli.commands.rule import RuleCommand
from src.cli.commands.status import StatusCommand
from src.cli.commands.task.task_command import TaskCommand
from src.cli.commands.template.template_command import TemplateCommand

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
COMMANDS: Dict[str, Type[Command]] = {
    "roadmap": RoadmapCommand,
    "rule": RuleCommand,
    "flow": FlowCommand,
    "status": StatusCommand,
    "task": TaskCommand,
    "memory": MemoryCommand,
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

    # 注册所有命令
    for cmd_name, cmd_class in COMMANDS.items():
        cli.add_command(create_cli_command(cmd_class), cmd_name)

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
    for cmd_name, cmd_class in COMMANDS.items():
        print(f"  {cmd_name:<10} {cmd_class.get_help()}")

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
