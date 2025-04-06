#!/usr/bin/env python3
"""
VibeCopilot - AI辅助项目管理工具

主入口文件
"""

import sys

from src.commands.cli import run_cli


def main():
    """主程序入口点"""
    run_cli()


if __name__ == "__main__":
    sys.exit(main())
