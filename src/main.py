#!/usr/bin/env python3
"""
VibeCopilot - AI辅助项目管理工具

主入口文件
"""

import logging
import sys

from src.commands.cli import run_cli

# 不在这里配置日志，让CLI根据--verbose选项来控制
logger = logging.getLogger(__name__)


def main():
    """主程序入口点"""
    # 运行CLI
    run_cli()


if __name__ == "__main__":
    sys.exit(main())
