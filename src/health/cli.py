#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import click
import yaml

from src.health.checkers.base_checker import CheckResult
from src.health.checkers.command_checker import CommandChecker
from src.health.checkers.database_checker import DatabaseChecker
from src.health.checkers.system_checker import SystemChecker


class HealthCheckCLI:
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(__file__), "config")

    def load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        config_path = os.path.join(self.config_dir, config_file)
        if not os.path.exists(config_path):
            click.echo(f"错误: 配置文件 {config_file} 不存在")
            sys.exit(1)

        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def run_system_check(self, verbose: bool = False) -> CheckResult:
        """运行系统检查"""
        config = self.load_config("system_check_config.yaml")
        checker = SystemChecker(config)
        return checker.check()

    def run_command_check(self, category: Optional[str] = None, verbose: bool = False) -> CheckResult:
        """运行命令检查"""
        # 加载主配置
        config = self.load_config("commands/config.yaml")

        # 加载所有命令组配置
        command_configs = {}
        for group in config["command_groups"]:
            group_config = self.load_config(f"commands/{group['config_file']}")
            command_configs[group["name"]] = group_config

        checker = CommandChecker(config, command_configs, category=category, verbose=verbose)
        return checker.check()

    def run_database_check(self, verbose: bool = False) -> CheckResult:
        """运行数据库检查"""
        config = self.load_config("database_check_config.yaml")
        checker = DatabaseChecker(config)
        return checker.check()

    def generate_report(self, results: Dict[str, CheckResult]) -> str:
        """生成检查报告"""
        report = []
        report.append("# VibeCopilot 系统健康检查报告")
        report.append(f"\n## 检查时间: {datetime.now().isoformat()}")

        # 计算总体状态
        overall_status = "passed"
        total_metrics = {"total": 0, "passed": 0, "failed": 0, "warnings": 0}

        for check_result in results.values():
            if check_result.status == "failed":
                overall_status = "failed"
            elif check_result.status == "warning" and overall_status != "failed":
                overall_status = "warning"

            # 累计统计数据
            if hasattr(check_result, "metrics") and isinstance(check_result.metrics, dict):
                for key, value in check_result.metrics.items():
                    if key in total_metrics:
                        total_metrics[key] += value

        report.append(f"## 整体状态: {overall_status.upper()}")

        report.append("\n## 统计摘要")
        report.append(f"- 总检查项: {total_metrics['total']}")
        report.append(f"- 通过: {total_metrics['passed']}")
        report.append(f"- 失败: {total_metrics['failed']}")
        report.append(f"- 警告: {total_metrics['warnings']}")

        report.append("\n## 详细检查结果")
        for module_name, check_result in results.items():
            report.append(f"\n### {module_name}")
            report.append(f"状态: {check_result.status.upper()}")

            if check_result.details:
                report.append("\n详细信息:")
                for detail in check_result.details:
                    if isinstance(detail, list):
                        for d in detail:
                            report.append(f"- {d}")
                    else:
                        report.append(f"- {detail}")

            if check_result.suggestions:
                report.append("\n建议:")
                for suggestion in check_result.suggestions:
                    if isinstance(suggestion, list):
                        for s in suggestion:
                            report.append(f"- {s}")
                    else:
                        report.append(f"- {suggestion}")

        return "\n".join(report)


@click.group()
def cli():
    """VibeCopilot 健康检查工具"""
    pass


@cli.command()
@click.option("--module", type=click.Choice(["system", "command", "database", "all"]), default="all", help="要检查的模块")
@click.option("--category", help="命令类别（仅用于命令检查）")
@click.option("--verbose", is_flag=True, help="显示详细信息")
def check(module: str, category: Optional[str], verbose: bool):
    """运行健康检查"""
    cli_tool = HealthCheckCLI()
    results: Dict[str, CheckResult] = {}

    try:
        if module in ["system", "all"]:
            results["系统检查"] = cli_tool.run_system_check(verbose)

        if module in ["command", "all"]:
            results["命令检查"] = cli_tool.run_command_check(category, verbose)

        if module in ["database", "all"]:
            results["数据库检查"] = cli_tool.run_database_check(verbose)

        # 生成并显示报告
        click.echo(cli_tool.generate_report(results))

        # 根据检查结果设置退出码
        has_failure = any(result.status == "failed" for result in results.values())
        sys.exit(1 if has_failure else 0)

    except Exception as e:
        click.echo(f"错误: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
