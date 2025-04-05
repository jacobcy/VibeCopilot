#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目管理命令行工具

提供访问scripts/github_project功能的命令行接口
"""

import argparse
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scripts.github.projects.analysis.cli import main as analysis_main


def main():
    """命令行主入口"""
    parser = argparse.ArgumentParser(description="GitHub项目管理工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 项目分析命令
    analysis_parser = subparsers.add_parser("analysis", help="项目分析与路线图调整")
    analysis_parser.add_argument("--help-analysis", action="store_true", help="显示分析模块帮助信息")

    # 解析参数
    args, extra_args = parser.parse_known_args()

    if not args.command:
        parser.print_help()
        return

    # 根据子命令调用相应模块
    if args.command == "analysis":
        if args.help_analysis:
            # 显示分析模块帮助
            sys.argv = [sys.argv[0], "--help"]
        else:
            # 将未解析的参数传递给分析模块
            sys.argv = [sys.argv[0]] + extra_args
        analysis_main()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
