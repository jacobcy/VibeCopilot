#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from src.health.cli_tools import HealthCheckCLI
from src.health.config_loader import load_config, load_module_config
from src.health.health_check import HealthCheck
from src.health.merge_commands import merge_command_files

logger = logging.getLogger(__name__)


@click.group()
def cli():
    """VibeCopilot 系统健康检查工具"""
    pass


@cli.command()
@click.option(
    "--module",
    type=click.Choice(["system", "command", "database", "status", "enabled_modules", "all"]),
    default="all",
    help="要检查的模块",
)
@click.option("--category", help="命令类别（仅用于命令检查）")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@click.option(
    "--format",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="报告输出格式",
)
@click.option("-o", "--output", help="报告输出文件路径")
@click.option("--use-llm", is_flag=True, default=False, help="使用 LLM 对比命令帮助信息 (实验性功能)")
def check(module: str, category: Optional[str], verbose: bool, format: str, output: Optional[str], use_llm: bool):
    """执行系统健康检查。

    可检查的模块包括:
    system (系统环境),
    command (命令完整性),
    database (数据库状态),
    status (状态模块模拟),
    enabled_modules (配置的启用模块),
    all (所有已启用模块)。
    """
    try:
        # 加载主配置
        config = load_config()
        if not config:
            click.echo("错误: 无法加载配置文件")
            return

        # 如果命令行指定了 --use-llm，则覆盖配置文件中的设置
        # 需要确保这个设置能传递给 CommandChecker
        # 最佳实践是修改传递给 HealthCheck 的 config 字典
        if use_llm:
            # Ensure 'command' key exists in config
            if "command" not in config:
                config["command"] = {}
            config["command"]["use_llm_comparison"] = True
            logger.info("通过命令行启用 LLM 命令帮助对比。")
            # Optionally ensure llm_config exists if needed, though CommandChecker should handle None
            # if 'llm_config' not in config['command']:
            #     logger.warning("LLM comparison enabled via CLI, but no llm_config found in main config.")
            #     config['command']['llm_config'] = {} # Provide default if needed
        else:
            # If CLI flag is false, ensure config reflects this if present
            if "command" in config:
                config["command"]["use_llm_comparison"] = False

        click.echo(f"正在执行 {module} 模块的健康检查... {'(使用 LLM 对比)' if use_llm else ''}")

        # 创建健康检查实例 (传递修改后的 config)
        health_check = HealthCheck(config)
        # Pass verbose flag to HealthCheck if it needs it (e.g., for CommandChecker)
        health_check.verbose = verbose

        # 创建CLI工具实例 (可能不再需要，因为检查逻辑在HealthCheck中)
        # cli_tool = HealthCheckCLI()

        # 根据module参数执行相应的检查
        if module == "all":
            result = health_check.check_all()
        else:
            # 单个模块检查
            # Pass category directly to check_module if it handles it,
            # otherwise HealthCheck needs to pass it to CommandChecker
            # Let's assume HealthCheck passes relevant context like category/verbose
            # HealthCheck's _get_checker for 'command' already takes category and verbose
            health_check.category = category  # Set category on the instance
            result = health_check.check_module(module)

            # --- Remove the special handling for 'command' here ---
            # --- Let HealthCheck handle getting the right checker ---
            # if module == "command":
            #     # ... old logic using cli_tool ...
            # else:
            #     result = health_check.check_module(module)

        # 确保结果状态不是unknown (这部分逻辑可以保留或移到HealthCheck内部)
        if hasattr(result, "status") and result.status == "unknown":
            if verbose:
                click.echo("警告: 检查结果状态为unknown，尝试修正...")
            if health_check.results["overall_status"] != "unknown":
                result.status = health_check.results["overall_status"]
            elif hasattr(result, "metrics"):
                metrics = result.metrics
                if metrics.get("failed", 0) > 0:
                    result.status = "failed"
                elif metrics.get("warnings", 0) > 0:
                    result.status = "warning"
                else:
                    result.status = "passed"

        # 生成报告
        report = health_check.generate_report(format=format, verbose=verbose)

        # 保存报告到data/reports目录
        reports_dir = Path("data/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_report_filename = f"health_report_{timestamp}.{format}"

        if output:
            # 如果用户指定了输出文件，使用用户指定的路径
            report_path = Path(output)
        else:
            # 否则使用默认路径
            report_path = reports_dir / default_report_filename

        # 保存报告
        report_path.write_text(report, encoding="utf-8")
        click.echo(f"报告已保存到: {report_path}")

        # 限制保存的报告数量为最新的10份
        reports = sorted(list(reports_dir.glob(f"health_report_*.{format}")), reverse=True)
        if len(reports) > 10:
            for old_report in reports[10:]:
                old_report.unlink()
                click.echo(f"已删除旧报告: {old_report}")

        # 输出报告
        click.echo(report)

        # 根据检查结果设置退出码 - 修改逻辑
        # 无论 result.status 是什么，只要检查过程没出错，就退出 0
        # 非零退出码仅用于表示 health check 命令本身的执行错误
        sys.exit(0)

    except ImportError as e:
        click.echo(f"错误: 缺少必要的依赖模块: {e}")
        sys.exit(3)  # 保留特定错误码
    except FileNotFoundError as e:
        click.echo(f"错误: 文件未找到: {e}")
        sys.exit(4)  # 保留特定错误码
    except json.JSONDecodeError as e:
        click.echo(f"错误: JSON格式错误: {e}")
        sys.exit(5)  # 保留特定错误码
    except Exception as e:
        click.echo(f"执行健康检查时发生错误: {e}")
        if verbose:
            click.echo(traceback.format_exc())
        sys.exit(10)  # 保留通用错误码


@cli.command()
@click.option("--list", "list_reports", is_flag=True, help="列出最近的报告")
@click.option("--format", type=click.Choice(["text", "json", "markdown"]), default=None, help="报告格式筛选")
@click.argument("report_name", required=False)
def report(list_reports, format, report_name):
    """查看或列出健康检查报告

    不带参数时，显示最新报告。使用--list查看所有报告列表。
    可以通过报告名称查看特定报告。
    """
    reports_dir = Path("data/reports")

    # 检查报告目录是否存在
    if not reports_dir.exists() or not reports_dir.is_dir():
        click.echo("报告目录不存在，还没有生成任何报告。")
        return

    # 获取所有报告文件
    all_reports = []
    for ext in ["markdown", "md", "json", "txt"]:
        if format and ext not in format:
            continue
        all_reports.extend(reports_dir.glob(f"health_report_*.{ext}"))

    # 按时间排序
    all_reports = sorted(all_reports, key=lambda x: x.stat().st_mtime, reverse=True)

    if not all_reports:
        click.echo("未找到任何报告文件。请先运行 health check 命令生成报告。")
        return

    # 列出所有报告
    if list_reports:
        click.echo("最近的健康检查报告:")
        for i, report_file in enumerate(all_reports, 1):
            report_time = datetime.fromtimestamp(report_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"{i}. {report_file.name} - {report_time}")
        return

    # 查看特定报告
    if report_name:
        # 尝试直接找到匹配的报告文件
        report_file = reports_dir / report_name
        if not report_file.exists():
            # 尝试根据输入的数字选择报告
            try:
                index = int(report_name) - 1
                if 0 <= index < len(all_reports):
                    report_file = all_reports[index]
                else:
                    click.echo(f"错误: 无效的报告索引 {report_name}，有效范围是 1-{len(all_reports)}")
                    return
            except ValueError:
                click.echo(f"错误: 未找到报告 {report_name}")
                return
    else:
        # 默认显示最新报告
        if all_reports:
            report_file = all_reports[0]
        else:
            click.echo("未找到任何报告文件。")
            return

    # 显示报告内容
    try:
        report_content = report_file.read_text(encoding="utf-8")
        click.echo(f"显示报告: {report_file.name}\n")
        click.echo(report_content)
    except Exception as e:
        click.echo(f"读取报告文件时出错: {e}")


@cli.command(name="merge-cmd")
@click.option("--dry-run", is_flag=True, help="只显示将要进行的更改，不实际执行")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@click.option("--force", is_flag=True, help="强制重写所有规则文件")
def merge_cmd(dry_run, verbose, force):
    """将命令配置文件同步到规则中

    读取src/health/config/commands目录中的命令配置，
    生成对应的规则文件到.cursor/rules/command-rules目录。
    """
    try:
        if dry_run:
            click.echo("执行命令同步 (仅模拟)")
        else:
            click.echo("执行命令同步...")
            result = merge_command_files(verbose=verbose, force=force)
            if verbose:
                click.echo(f"处理了 {result['total_files']} 个文件，共 {result['total_commands']} 个命令")
                if result["failed"]:
                    click.echo(f"失败: {len(result['failed'])} 个文件")
                    for fail in result["failed"]:
                        click.echo(f"  - {fail['path']}: {fail['error']}")
            click.echo("命令同步完成")
    except Exception as e:
        click.echo(f"命令同步失败: {e}")
        sys.exit(1)


def main():
    """入口函数"""
    cli()


if __name__ == "__main__":
    main()
