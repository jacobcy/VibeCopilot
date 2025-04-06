#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主入口模块.

提供命令行工具的主入口点，整合参数解析、配置加载和命令执行。
"""

import logging

from .args import parse_args
from .commands import adjust_timeline, analyze_project, apply_updates
from .config import load_config
from .logging_setup import setup_logging
from .reports import generate_report


def main():
    """主函数.

    解析命令行参数，加载配置，并执行相应的命令。
    """
    # 解析命令行参数
    args = parse_args()

    # 设置日志
    setup_logging(getattr(args, "verbose", False))

    # 加载配置
    config = load_config()

    # 执行命令
    if args.command == "analyze":
        analyze_project(args, config)
    elif args.command == "adjust":
        adjust_timeline(args, config)
    elif args.command == "apply":
        apply_updates(args, config)
    elif args.command == "report":
        generate_report(args)
    else:
        print("请指定子命令: analyze, adjust, apply, report")
        print("使用 --help 查看帮助")


if __name__ == "__main__":
    main()
