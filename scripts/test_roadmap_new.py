#!/usr/bin/env python3
"""
新版路线图命令测试脚本

用于测试新版Click实现的路线图命令。
此脚本可以直接运行，不会影响原来的命令实现。
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.cli.commands.roadmap_new.roadmap_click import roadmap

if __name__ == "__main__":
    # 移除脚本名称
    args = sys.argv[1:]

    # 使用click的invoke方法手动调用命令
    if not args:
        # 如果没有参数，显示帮助
        roadmap(["--help"])
    else:
        # 否则执行命令
        roadmap(args)
