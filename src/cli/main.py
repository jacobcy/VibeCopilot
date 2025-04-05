#!/usr/bin/env python
"""
命令行入口模块

提供命令行工具的主入口，处理命令行参数并调用对应的命令处理器。
"""

import logging
import sys
from typing import List

from src.cli.command_parser import CommandParser
from src.cli.commands import *  # 导入所有命令
from src.cli.commands.rule_command import RuleCommand

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main(args: List[str] = None) -> int:
    """主入口函数

    Args:
        args: 命令行参数，如果为None则使用sys.argv

    Returns:
        int: 执行结果，0表示成功，非0表示失败
    """
    if args is None:
        args = sys.argv[1:]

    # 创建命令解析器
    parser = CommandParser()

    # 注册命令
    from src.cli.commands.db import DatabaseCommand

    parser.register_command(DatabaseCommand())
    parser.register_command(RuleCommand())  # 注册规则命令

    # 解析并执行命令
    return parser.parse_and_execute(args)


if __name__ == "__main__":
    sys.exit(main())
