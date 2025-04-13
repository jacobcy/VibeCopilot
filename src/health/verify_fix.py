#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""验证命令检查器修复效果的脚本"""

import json
import os
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置日志级别
import logging

import yaml

from src.health.checkers.command_checker import CommandChecker
from src.health.health_check import HealthCheck

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def load_config(config_path):
    """加载配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_command_checker():
    """测试命令检查器"""
    print("\n==== 测试命令检查器 ====")

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
    print(f"指标: {result.metrics}")

    if hasattr(result, "command_results"):
        print("\n命令检查结果:")
        for cmd, cmd_result in result.command_results.items():
            status = cmd_result.get("status", "unknown")
            print(f"- {cmd}: {status}")
            if isinstance(cmd_result, dict):
                if "errors" in cmd_result and cmd_result["errors"]:
                    for error in cmd_result["errors"]:
                        print(f"  - 错误: {error}")

    # 验证结果
    assert result.status != "unknown", "状态仍然为unknown!"
    print("✅ 验证通过: 状态不是unknown")

    # 测试通过
    return True


def test_health_check():
    """测试健康检查主类中的命令检查处理"""
    print("\n==== 测试健康检查集成 ====")

    # 加载配置
    config_dir = Path(__file__).parent / "config"

    try:
        # 首先尝试加载完整配置
        with open(config_dir / "check_config.yaml", "r", encoding="utf-8") as f:
            full_config = yaml.safe_load(f)
    except Exception as e:
        # 如果失败，则创建一个最小配置
        print(f"加载配置文件失败: {e}，使用最小配置")
        full_config = {
            "enabled_modules": ["command"],
            "command": {
                "common_config": {"command_prefix": "vibecopilot"},
                "performance": {"max_response_time": 30},
                "required_commands": [{"name": "help", "type": "command", "expected_output": ["usage", "help"]}],
            },
        }

    # 创建健康检查实例
    health_check = HealthCheck(full_config)

    # 执行命令模块检查
    result = health_check.check_module("command")

    # 打印结果
    print(f"检查状态: {result.status}")
    print(f"详细信息: {result.details}")

    # 检查结果是否为unknown
    assert result.status != "unknown", "命令检查状态仍然为unknown!"
    print("✅ 验证通过: 命令检查状态不是unknown")

    # 检查健康检查实例中的状态
    overall_status = health_check.results["overall_status"]
    print(f"健康检查整体状态: {overall_status}")
    assert overall_status != "unknown", "健康检查整体状态仍然为unknown!"
    print("✅ 验证通过: 健康检查整体状态不是unknown")

    # 生成报告并打印
    report = health_check.generate_report(format="text", verbose=True)
    print("\n生成的报告:")
    print("-" * 40)
    print(report)
    print("-" * 40)

    # 测试通过
    return True


if __name__ == "__main__":
    print("命令检查器修复验证脚本")
    print("=====================")

    try:
        # 运行测试
        command_test_ok = test_command_checker()
        health_test_ok = test_health_check()

        # 输出总结
        print("\n==== 验证结果 ====")
        print(f"命令检查器测试: {'✅ 通过' if command_test_ok else '❌ 失败'}")
        print(f"健康检查集成测试: {'✅ 通过' if health_test_ok else '❌ 失败'}")

        if command_test_ok and health_test_ok:
            print("\n🎉 所有测试通过! 命令检查器修复成功!")
            sys.exit(0)
        else:
            print("\n❌ 部分测试失败，需要进一步修复")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 验证过程出错: {e}")
        import traceback

        print(traceback.format_exc())
        sys.exit(2)
