#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""健康检查测试脚本"""

import os
import sys
from pathlib import Path

import yaml

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.health.checkers.command_checker import CommandChecker
from src.health.checkers.enabled_modules_checker import EnabledModulesChecker
from src.health.health_check import HealthCheck


def load_config(config_file: str):
    """加载配置文件"""
    config_dir = Path(__file__).parent / "config"
    config_path = config_dir / config_file

    if not config_path.exists():
        print(f"错误: 配置文件 {config_file} 不存在: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_command_checker():
    """测试命令检查器"""
    print("测试命令检查器...")

    # 加载配置
    config = load_config("commands/config.yaml")

    # 创建检查器
    checker = CommandChecker(config, {}, verbose=True)

    # 执行检查
    result = checker.check()

    # 打印结果
    print(f"命令检查结果: {result.status}")
    if result.details:
        print("详细信息:")
        for detail in result.details:
            print(f"- {detail}")

    if result.suggestions:
        print("建议:")
        for suggestion in result.suggestions:
            print(f"- {suggestion}")

    print(f"指标: {result.metrics}")


def test_enabled_modules_checker():
    """测试模块检查器"""
    print("测试已启用模块检查器...")

    # 加载配置
    config = load_config("enabled_modules_config.yaml")

    # 创建检查器
    checker = EnabledModulesChecker(config, verbose=True)

    # 执行检查
    result = checker.check()

    # 打印结果
    print(f"模块检查结果: {result.status}")
    if result.details:
        print("详细信息:")
        for detail in result.details:
            print(f"- {detail}")

    if result.suggestions:
        print("建议:")
        for suggestion in result.suggestions:
            print(f"- {suggestion}")

    print(f"指标: {result.metrics}")


def test_health_check():
    """测试健康检查主类"""
    print("测试健康检查主类...")

    # 加载配置
    global_config = {}

    # 配置文件映射
    config_file_map = {
        "system": "system_check_config.yaml",
        "command": "commands/config.yaml",
        "database": "database_check_config.yaml",
        "status": "status_check_config.yaml",
        "enabled_modules": "enabled_modules_config.yaml",
    }

    # 加载各模块配置
    for module in ["system", "command", "database", "status", "enabled_modules"]:
        try:
            config_file = config_file_map.get(module, f"{module}_config.yaml")

            module_config = load_config(config_file)
            global_config[module] = module_config
            print(f"已加载 {module} 模块配置")
        except Exception as e:
            print(f"加载 {module} 模块配置失败: {e}")

    # 创建健康检查
    health_check = HealthCheck(global_config)

    # 运行检查
    for module in ["enabled_modules"]:
        try:
            print(f"\n正在检查 {module} 模块...")
            result = health_check.check_module(module)
            print(f"检查结果: {result.status}")

            if result.details:
                print("详细信息:")
                for detail in result.details:
                    print(f"- {detail}")

            if result.suggestions:
                print("建议:")
                for suggestion in result.suggestions:
                    print(f"- {suggestion}")
        except Exception as e:
            print(f"检查 {module} 模块时出错: {e}")

    # 生成报告
    report = health_check.generate_report(format="markdown", verbose=True)
    print("\n健康检查报告:")
    print(report)


if __name__ == "__main__":
    print("VibeCopilot 健康检查测试")
    print("========================")

    # 根据命令行参数决定执行哪个测试
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "command":
            test_command_checker()
        elif test_name == "modules":
            test_enabled_modules_checker()
        elif test_name == "health":
            test_health_check()
        else:
            print(f"未知的测试: {test_name}")
            print("可用测试: command, modules, health")
    else:
        # 默认执行所有测试
        # test_command_checker()
        # test_enabled_modules_checker()
        test_health_check()
