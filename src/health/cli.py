#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import click
import yaml

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

    def run_system_check(self, verbose: bool = False) -> Dict:
        """运行系统检查"""
        config = self.load_config("system_check_config.yaml")
        checker = SystemChecker(config)
        return checker.run_checks(verbose)

    def run_command_check(self, category: Optional[str] = None, verbose: bool = False) -> Dict:
        """运行命令检查"""
        # 加载主配置
        config = self.load_config("commands/config.yaml")

        # 加载所有命令组配置
        command_configs = {}
        for group in config["command_groups"]:
            group_config = self.load_config(f"commands/{group['config_file']}")
            command_configs[group["name"]] = group_config

        checker = CommandChecker(config, command_configs)
        return checker.run_checks(category, verbose)

    def run_database_check(self, verbose: bool = False) -> Dict:
        """运行数据库检查"""
        config = self.load_config("database_check_config.yaml")
        checker = DatabaseChecker(config)
        return checker.run_checks(verbose)

    def generate_report(self, results: Dict) -> str:
        """生成检查报告"""
        report = []
        report.append("# VibeCopilot 系统健康检查报告")
        report.append(f"\n## 检查时间: {datetime.now().isoformat()}")
        report.append(f"## 整体状态: {results['overall_status'].upper()}")

        report.append("\n## 统计摘要")
        report.append(f"- 总检查项: {results['summary']['total']}")
        report.append(f"- 通过: {results['summary']['passed']}")
        report.append(f"- 失败: {results['summary']['failed']}")
        report.append(f"- 警告: {results['summary']['warnings']}")

        report.append("\n## 详细检查结果")
        for check in results["checks"]:
            report.append(f"\n### {check['name']}")
            report.append(f"状态: {check['status'].upper()}")

            if check["details"]:
                report.append("\n详细信息:")
                for detail in check["details"]:
                    report.append(f"- {detail}")

            if check["suggestions"]:
                report.append("\n建议:")
                for suggestion in check["suggestions"]:
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
    results = {"checks": [], "summary": {"total": 0, "passed": 0, "failed": 0, "warnings": 0}}

    try:
        if module in ["system", "all"]:
            sys_results = cli_tool.run_system_check(verbose)
            results["checks"].extend(sys_results["checks"])
            for key in results["summary"]:
                results["summary"][key] += sys_results["summary"][key]

        if module in ["command", "all"]:
            cmd_results = cli_tool.run_command_check(category, verbose)
            results["checks"].extend(cmd_results["checks"])
            for key in results["summary"]:
                results["summary"][key] += cmd_results["summary"][key]

        if module in ["database", "all"]:
            db_results = cli_tool.run_database_check(verbose)
            results["checks"].extend(db_results["checks"])
            for key in results["summary"]:
                results["summary"][key] += db_results["summary"][key]

        # 设置整体状态
        if results["summary"]["failed"] > 0:
            results["overall_status"] = "failed"
        elif results["summary"]["warnings"] > 0:
            results["overall_status"] = "warning"
        else:
            results["overall_status"] = "passed"

        # 生成并显示报告
        click.echo(cli_tool.generate_report(results))

        # 根据检查结果设置退出码
        sys.exit(0 if results["overall_status"] == "passed" else 1)

    except Exception as e:
        click.echo(f"错误: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
