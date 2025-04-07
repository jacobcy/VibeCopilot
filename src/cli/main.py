#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行入口模块

提供命令行工具的主入口，处理命令行参数并调用对应的命令处理器。
"""

import importlib
import logging
import os
import sys
from typing import Dict, Type

# 确保src目录在Python路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.cli.command import Command
from src.cli.command_parser import CommandParser
from src.cli.commands import RoadmapCommands
from src.cli.commands.db import DatabaseCommand
from src.cli.commands.flow.flow_command import FlowCommand
from src.cli.commands.help.help_command import HelpCommand
from src.cli.commands.memory import MemoryCommand
from src.cli.commands.rule import RuleCommand
from src.cli.commands.status import StatusCommand

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def main():
    """
    CLI主入口
    """
    # 注册命令
    commands: Dict[str, Type[Command]] = {
        "roadmap": RoadmapCommands,
        "rule": RuleCommand,
        "flow": FlowCommand,
        "status": StatusCommand,
        "memory": MemoryCommand,
        "db": DatabaseCommand,
        "help": HelpCommand,
        # 可以添加更多命令
    }

    # 解析命令
    parser = CommandParser()
    command_name, args = parser.parse_command()

    # 查找命令处理器
    command_class = commands.get(command_name)
    if not command_class:
        logger.error(f"未知命令: {command_name}")
        HelpCommand().execute([])
        return 1

    # 执行命令
    command = command_class()
    try:
        return command.execute(args)
    except Exception as e:
        logger.exception(f"执行命令失败: {str(e)}")
        return 1


def print_help():
    """打印帮助信息"""
    print("VibeCopilot CLI工具")
    print("\n可用命令:")
    print("  help        显示帮助信息")
    print("  roadmap     路线图管理命令")
    print("  rule        规则管理命令")
    print("  flow        工作流管理命令")
    print("  status      状态管理命令")
    print("  db          数据库管理命令")
    print("  memory      知识库管理命令")

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
