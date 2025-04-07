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
from src.cli.commands.flow.flow_command import FlowCommand
from src.cli.commands.help.help_command import HelpCommand
from src.cli.commands.rule import RuleCommand

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
    print("  roadmap     路线图管理命令")
    print("  rule        规则管理命令")
    print("  flow        流程管理命令")

    print("\n用法:")
    print("  vibecopilot <命令> [参数]")
    print("  vibecopilot roadmap sync github push")
    print("  vibecopilot roadmap story S1")
    print("  vibecopilot rule list")
    print("  vibecopilot flow start")


if __name__ == "__main__":
    sys.exit(main())
