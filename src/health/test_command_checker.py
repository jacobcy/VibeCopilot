#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""命令检查器测试脚本"""

import os
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import yaml

from src.health.checkers.command_checker import CommandChecker
from src.health.cli import HealthCheckCLI


def load_config(config_path):
    """加载配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_command_checker_simple():
    """测试命令检查器简单版本"""
    print("\n=== 测试命令检查器(简单版本) ===")

    # 创建简单的测试配置
    config = {"common_config": {"command_prefix": "vibecopilot"}, "performance": {"max_response_time": 30}}

    # 创建命令配置列表
    command_configs = [
        {"name": "help", "type": "command", "expected_output": ["usage", "help"]},
        {"name": "version", "type": "command", "expected_output": ["version"]},
    ]

    # 创建检查器
    checker = CommandChecker(config, command_configs, verbose=True)

    # 执行检查
    result = checker.check()

    # 打印结果
    print(f"检查状态: {result.status}")
    print(f"详细信息: {result.details}")
    print(f"建议: {result.suggestions}")
    print(f"指标: {result.metrics}")

    if hasattr(result, "command_results"):
        print("\n命令检查结果:")
        for cmd, cmd_result in result.command_results.items():
            print(f"- {cmd}: {cmd_result.get('status', 'unknown')}")


def test_command_checker_cli():
    """测试CLI中的命令检查器"""
    print("\n=== 测试CLI命令检查器 ===")

    cli = HealthCheckCLI()
    result = cli.run_command_check(verbose=True)

    print(f"检查状态: {result.status}")

    if result.details:
        print("详细信息:")
        for detail in result.details:
            print(f"- {detail}")

    if result.suggestions:
        print("建议:")
        for suggestion in result.suggestions:
            print(f"- {suggestion}")

    print(f"指标: {result.metrics}")


if __name__ == "__main__":
    print("命令检查器测试脚本")
    print("===============")

    # 测试简单版本
    test_command_checker_simple()

    # 测试CLI版本
    test_command_checker_cli()
