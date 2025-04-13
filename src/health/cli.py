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
        try:
            # 加载主配置
            config = self.load_config("commands/config.yaml")
            if verbose:
                group_count = len(config.get("command_groups", []))
                click.echo(f"已加载主配置文件: {group_count} 个命令组")

            # 加载所有命令组配置
            command_configs = {}
            for group in config.get("command_groups", []):
                try:
                    group_name = group.get("name")
                    config_file = group.get("config_file")
                    if not group_name or not config_file:
                        raise ValueError(f"命令组配置不完整: {group}")

                    if verbose:
                        click.echo(f"正在加载命令组配置: {group_name} ({config_file})")

                    group_config = self.load_config(f"commands/{config_file}")
                    command_configs[group_name] = group_config

                    if verbose:
                        click.echo(f"成功加载命令组 {group_name} 的配置")
                except Exception as e:
                    raise ValueError(f"加载命令组 {group_name} 配置失败: {str(e)}")

            checker = CommandChecker(config, command_configs, category=category, verbose=verbose)
            return checker.check()
        except Exception as e:
            error_msg = f"命令检查失败: {str(e)}"
            if verbose:
                import traceback

                error_msg += f"\n详细错误信息:\n{traceback.format_exc()}"
            raise Exception(error_msg)

    def run_database_check(self, verbose: bool = False) -> CheckResult:
        """运行数据库检查"""
        config = self.load_config("database_check_config.yaml")
        checker = DatabaseChecker(config)
        return checker.check()

    def generate_report(self, results: Dict[str, CheckResult], format: str = "markdown") -> str:
        """生成检查报告

        Args:
            results: 检查结果字典
            format: 报告格式，可选 "text" 或 "markdown"

        Returns:
            str: 生成的报告内容
        """
        if format == "text":
            return self._generate_text_report(results)
        else:  # markdown
            return self._generate_markdown_report(results)

    def _generate_markdown_report(self, results: Dict[str, CheckResult]) -> str:
        """生成Markdown格式的检查报告"""
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

        report.append(f"\n## 整体状态: {overall_status.upper()}")

        report.append("\n## 统计摘要")
        report.append(f"- 总检查项: {total_metrics['total']}")
        report.append(f"- 通过: {total_metrics['passed']}")
        report.append(f"- 失败: {total_metrics['failed']}")
        report.append(f"- 警告: {total_metrics['warnings']}")

        report.append("\n## 详细检查结果")
        for module_name, check_result in results.items():
            report.append(f"\n### {module_name}")
            report.append(f"状态: {check_result.status.upper()}")

            if module_name == "命令检查" and hasattr(check_result, "command_results"):
                report.append("\n命令组检查详情:")
                for group_name, group_result in check_result.command_results.items():
                    report.append(f"\n#### {group_name}")
                    status_icon = "✅" if group_result.get("status") == "passed" else "❌"
                    report.append(f"{status_icon} 状态: {group_result.get('status', 'unknown').upper()}")

                    if "commands" in group_result:
                        failed_commands = [(cmd, result) for cmd, result in group_result["commands"].items() if result.get("status") != "passed"]

                        if failed_commands:
                            report.append("\n失败的命令:")
                            for cmd, cmd_result in failed_commands:
                                report.append(f"❌ {cmd}")
                                if "errors" in cmd_result:
                                    for error in cmd_result["errors"]:
                                        if isinstance(error, str) and "错误代码" in error:
                                            continue
                                        report.append(f"  - {error}")
                                if "warnings" in cmd_result:
                                    for warning in cmd_result["warnings"]:
                                        report.append(f"  - 警告: {warning}")

                        passed_commands = [(cmd, result) for cmd, result in group_result["commands"].items() if result.get("status") == "passed"]
                        if passed_commands:
                            report.append("\n通过的命令:")
                            for cmd, _ in passed_commands:
                                report.append(f"✅ {cmd}")

            if check_result.details:
                report.append("\n详细信息:")
                for detail in check_result.details:
                    if isinstance(detail, list):
                        for d in detail:
                            report.append(f"- {d}")
                    else:
                        report.append(f"- {detail}")

            if check_result.suggestions:
                report.append("\n改进建议:")
                unique_suggestions = []
                for suggestion in check_result.suggestions:
                    if isinstance(suggestion, list):
                        unique_suggestions.extend(s for s in suggestion if s not in unique_suggestions)
                    elif suggestion not in unique_suggestions:
                        unique_suggestions.append(suggestion)
                for suggestion in unique_suggestions:
                    report.append(f"- {suggestion}")

        return "\n".join(report)

    def _generate_text_report(self, results: Dict[str, CheckResult]) -> str:
        """生成纯文本格式的检查报告"""
        report = []
        report.append("VibeCopilot 系统健康检查报告")
        report.append("============================")
        report.append(f"检查时间: {datetime.now().isoformat()}")
        report.append("")

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

        report.append(f"整体状态: {overall_status.upper()}")
        report.append("")

        report.append("统计摘要:")
        report.append(f"- 总检查项: {total_metrics['total']}")
        report.append(f"- 通过: {total_metrics['passed']}")
        report.append(f"- 失败: {total_metrics['failed']}")
        report.append(f"- 警告: {total_metrics['warnings']}")
        report.append("")

        report.append("详细检查结果:")
        for module_name, check_result in results.items():
            report.append("")
            report.append(f"{module_name}")
            report.append("-" * len(module_name))
            report.append(f"状态: {check_result.status.upper()}")

            if module_name == "命令检查" and hasattr(check_result, "command_results"):
                report.append("\n命令组检查详情:")
                for group_name, group_result in check_result.command_results.items():
                    report.append(f"\n{group_name}:")
                    status_icon = "✓" if group_result.get("status") == "passed" else "✗"
                    report.append(f"{status_icon} 状态: {group_result.get('status', 'unknown').upper()}")

                    if "commands" in group_result:
                        failed_commands = [(cmd, result) for cmd, result in group_result["commands"].items() if result.get("status") != "passed"]

                        if failed_commands:
                            report.append("\n失败的命令:")
                            for cmd, cmd_result in failed_commands:
                                report.append(f"✗ {cmd}")
                                if "errors" in cmd_result:
                                    for error in cmd_result["errors"]:
                                        if isinstance(error, str) and "错误代码" in error:
                                            continue
                                        report.append(f"  - {error}")
                                if "warnings" in cmd_result:
                                    for warning in cmd_result["warnings"]:
                                        report.append(f"  - 警告: {warning}")

                        passed_commands = [(cmd, result) for cmd, result in group_result["commands"].items() if result.get("status") == "passed"]
                        if passed_commands:
                            report.append("\n通过的命令:")
                            for cmd, _ in passed_commands:
                                report.append(f"✓ {cmd}")

            if check_result.details:
                report.append("\n详细信息:")
                for detail in check_result.details:
                    if isinstance(detail, list):
                        for d in detail:
                            report.append(f"- {d}")
                    else:
                        report.append(f"- {detail}")

            if check_result.suggestions:
                report.append("\n改进建议:")
                unique_suggestions = []
                for suggestion in check_result.suggestions:
                    if isinstance(suggestion, list):
                        unique_suggestions.extend(s for s in suggestion if s not in unique_suggestions)
                    elif suggestion not in unique_suggestions:
                        unique_suggestions.append(suggestion)
                for suggestion in unique_suggestions:
                    report.append(f"- {suggestion}")

        return "\n".join(report)


@click.group()
def cli():
    """VibeCopilot 健康检查工具

    提供以下功能:
    - check: 运行健康检查并生成报告
    - report-example: 显示健康检查报告示例
    - report-help: 显示健康检查报告格式说明

    使用示例:
    python -m src.health.cli check --module all --format markdown --output health_report.md
    """
    pass


@cli.command()
@click.option("--module", type=click.Choice(["system", "command", "database", "all"]), default="all", help="要检查的模块")
@click.option("--category", help="命令类别（仅用于命令检查）")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["text", "markdown"]), default="markdown", help="报告输出格式")
@click.option("--output", "-o", help="报告输出文件路径，不指定则输出到控制台")
def check(module: str, category: Optional[str], verbose: bool, format: str, output: Optional[str]):
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

        # 生成报告
        report = cli_tool.generate_report(results, format)

        # 如果指定了输出文件，则写入文件
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(report)
            click.echo(f"报告已写入文件: {output}")
        else:
            # 否则输出到控制台
            click.echo(report)

        # 根据检查结果设置退出码
        has_failure = any(result.status == "failed" for result in results.values())
        sys.exit(1 if has_failure else 0)

    except Exception as e:
        click.echo(f"错误: {str(e)}", err=True)
        sys.exit(1)


@cli.command(name="report-help")
@click.option("--format", type=click.Choice(["text", "markdown"]), default="text", help="输出格式")
def report_help(format: str):
    """显示健康检查报告格式说明"""
    if format == "text":
        click.echo(
            """
健康检查报告格式说明:

1. 报告头部
   - 检查时间
   - 整体状态 (PASSED/WARNING/FAILED)

2. 统计摘要
   - 总检查项数量
   - 通过的检查项数量
   - 失败的检查项数量
   - 警告的检查项数量

3. 详细检查结果
   - 系统检查结果
   - 命令检查结果
   - 数据库检查结果

4. 每个检查项包含
   - 状态图标 (✅ 通过, ❌ 失败, ⚠️ 警告)
   - 详细信息
   - 错误信息（如果有）
   - 警告信息（如果有）
   - 建议（如果有）

使用示例:
python -m src.health.cli check --module all --format markdown --output health_report.md
python -m src.health.cli report-example --format text
        """
        )
    else:
        click.echo(
            """
# 健康检查报告格式说明

## 报告结构

### 1. 报告头部
- 检查时间
- 整体状态 (PASSED/WARNING/FAILED)

### 2. 统计摘要
- 总检查项数量
- 通过的检查项数量
- 失败的检查项数量
- 警告的检查项数量

### 3. 详细检查结果
每个模块的检查结果，包括：
- 系统检查
- 命令检查
- 数据库检查

### 4. 检查项格式
- ✅ 表示通过
- ❌ 表示失败
- ⚠️ 表示警告
- 包含详细信息、错误、警告和建议

## 使用示例
```bash
# 运行检查并生成markdown报告
python -m src.health.cli check --module all --format markdown --output health_report.md

# 查看示例报告
python -m src.health.cli report-example --format text
```
        """
        )


@cli.command(name="report-example")
@click.option("--format", type=click.Choice(["text", "markdown"]), default="markdown", help="输出格式")
def report_example(format: str):
    """显示健康检查报告示例"""
    cli_tool = HealthCheckCLI()

    # 创建示例结果
    from collections import namedtuple

    # 创建一个简单的CheckResult数据结构
    MockCheckResult = namedtuple("MockCheckResult", ["status", "details", "suggestions", "metrics", "command_results"])

    # 创建样例数据
    system_result = MockCheckResult(
        status="passed",
        details=["系统环境检查通过", "Python版本: 3.9.6", "操作系统: Linux"],
        suggestions=["建议更新至Python 3.10以获得更好的性能"],
        metrics={"total": 5, "passed": 5, "failed": 0, "warnings": 0},
        command_results=None,
    )

    db_result = MockCheckResult(
        status="warning",
        details=["数据库连接正常", "数据库版本: SQLite 3.36.0", "发现2个未使用的表"],
        suggestions=["清理未使用的表以提高性能", "考虑添加更多索引"],
        metrics={"total": 8, "passed": 6, "failed": 0, "warnings": 2},
        command_results=None,
    )

    # 命令检查结果更复杂，包含命令组和命令详情
    command_results = {
        "任务管理": {
            "status": "passed",
            "commands": {"task create": {"status": "passed"}, "task list": {"status": "passed"}, "task update": {"status": "passed"}},
        },
        "规则管理": {
            "status": "failed",
            "commands": {
                "rule list": {"status": "passed"},
                "rule create": {"status": "failed", "errors": ["缺少必要参数", "错误代码: 1001"]},
                "rule update": {"status": "warning", "warnings": ["性能较慢"]},
            },
        },
    }

    command_result = MockCheckResult(
        status="failed",
        details=["命令检查发现错误", "1个命令组失败", "1个命令组通过"],
        suggestions=["修复rule create命令中的参数检查逻辑"],
        metrics={"total": 6, "passed": 4, "failed": 1, "warnings": 1},
        command_results=command_results,
    )

    # 合并结果
    results = {"系统检查": system_result, "数据库检查": db_result, "命令检查": command_result}

    # 生成并显示报告
    report = cli_tool.generate_report(results, format)
    click.echo(report)


def main():
    """入口函数"""
    cli()


if __name__ == "__main__":
    main()
