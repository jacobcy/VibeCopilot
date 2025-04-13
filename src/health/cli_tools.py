"""
健康检查CLI工具模块
"""
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, List, Optional

import click
import yaml

from src.health.checkers.base_checker import CheckResult
from src.health.checkers.command_checker import CommandChecker
from src.health.checkers.database_checker import DatabaseChecker
from src.health.checkers.system_checker import SystemChecker


class HealthCheckCLI:
    """健康检查CLI工具类，提供单独的模块检查功能"""

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
                        if verbose:
                            click.echo(f"警告: 命令组配置不完整: {group}")
                        continue

                    if verbose:
                        click.echo(f"正在加载命令组配置: {group_name} ({config_file})")

                    try:
                        config_path = f"commands/{config_file}"
                        group_config = self.load_config(config_path)
                        command_configs[group_name] = group_config

                        if verbose:
                            click.echo(f"成功加载命令组 {group_name} 的配置")
                    except Exception as e:
                        if verbose:
                            click.echo(f"警告: 无法加载配置文件 {config_path}: {str(e)}")
                        continue
                except Exception as e:
                    if verbose:
                        click.echo(f"警告: 处理命令组时出错: {str(e)}")
                    continue

            # 尝试创建并运行检查器
            try:
                checker = CommandChecker(config, command_configs, category=category, verbose=verbose)
                return checker.check()
            except Exception as e:
                error_msg = f"命令检查器执行失败: {str(e)}"
                if verbose:
                    error_msg += f"\n详细错误信息:\n{traceback.format_exc()}"

                # 返回失败结果而不是抛出异常
                return CheckResult(
                    status="failed",
                    details=[error_msg],
                    suggestions=["检查命令配置和实现"],
                    metrics={"total": 1, "passed": 0, "failed": 1, "warnings": 0},
                    command_results={},
                )
        except Exception as e:
            error_msg = f"命令检查失败: {str(e)}"
            if verbose:
                error_msg += f"\n详细错误信息:\n{traceback.format_exc()}"

            # 返回失败结果而不是抛出异常
            return CheckResult(
                status="failed",
                details=[error_msg],
                suggestions=["检查命令检查模块"],
                metrics={"total": 1, "passed": 0, "failed": 1, "warnings": 0},
                command_results={},
            )

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
