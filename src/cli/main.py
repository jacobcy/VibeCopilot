#!/usr/bin/env python
"""
命令行入口模块

提供命令行工具的主入口，处理命令行参数并调用对应的命令处理器。
"""

import logging
import os
import sys
from typing import Dict, Type

# 确保src目录在Python路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.cli.command import Command
from src.cli.commands import RoadmapCommands, RuleCommand

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
    # 获取命令行参数（跳过脚本名称）
    args = sys.argv[1:]

    if not args:
        print_help()
        return 1

    # 获取命令名称
    command_name = args.pop(0)

    # 注册所有命令
    commands: Dict[str, Type[Command]] = {"roadmap": RoadmapCommands, "rule": RuleCommand}

    # 检查命令是否存在
    if command_name not in commands:
        print(f"错误: 未知的命令 '{command_name}'")
        print_help()
        return 1

    # 创建命令实例
    command = commands[command_name]()

    try:
        # 解析参数
        parsed_args = command.parse_args(args)
        # 执行命令
        command.execute(parsed_args)
        return 0
    except Exception as e:
        logger.error(f"命令执行失败: {str(e)}")
        return 1


def print_help():
    """打印帮助信息"""
    print("VibeCopilot CLI工具")
    print("\n可用命令:")
    print("  roadmap     路线图管理命令")
    print("  rule        规则管理命令")

    print("\n用法:")
    print("  vibecopilot <命令> [参数]")
    print("  vibecopilot roadmap sync github push")
    print("  vibecopilot roadmap story S1")
    print("  vibecopilot rule list")


if __name__ == "__main__":
    sys.exit(main())
