#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import sys
import traceback
from typing import Optional

import click

from src.health.cli_tools import HealthCheckCLI
from src.health.config_loader import load_config, load_module_config
from src.health.health_check import HealthCheck
from src.health.report_commands import report_example, report_help

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
def check(module: str, category: Optional[str], verbose: bool, format: str, output: Optional[str]):
    """执行系统健康检查

    说明：
    目前已实现的检查器模块包括：
    - system: 系统环境检查
    - command: 命令完整性检查
    - database: 数据库状态检查
    - status: 状态模块健康检查
    - enabled_modules: 启用模块检查

    配置文件中引用但尚未实现的检查器包括：
    - general, global, report, notifications, documentation
    """
    try:
        # 加载配置
        config = load_config()
        if not config:
            click.echo("错误: 无法加载配置文件")
            return

        click.echo(f"正在执行{module}模块的健康检查...")

        # 创建健康检查实例
        health_check = HealthCheck(config)

        # 创建CLI工具实例
        cli_tool = HealthCheckCLI()

        # 根据module参数执行相应的检查
        if module == "all":
            # 执行所有模块检查
            result = health_check.check_all()
        else:
            # 单个模块检查
            # 如果是命令检查且有category参数，需要单独处理
            if module == "command":
                # 加载命令检查配置
                cmd_config = load_module_config("command")

                # 执行命令检查
                result = cli_tool.run_command_check(category=category, verbose=verbose)

                # 更新健康检查结果
                health_check._update_results("command", result)
            else:
                # 其他模块检查
                result = health_check.check_module(module)

        # 确保结果状态不是unknown
        if hasattr(result, "status") and result.status == "unknown":
            if verbose:
                click.echo("警告: 检查结果状态为unknown，尝试修正...")
            # 从health_check中获取real_status
            if health_check.results["overall_status"] != "unknown":
                result.status = health_check.results["overall_status"]
            else:
                # 尝试从metrics推断状态
                if hasattr(result, "metrics"):
                    metrics = result.metrics
                    if metrics.get("failed", 0) > 0:
                        result.status = "failed"
                    elif metrics.get("warnings", 0) > 0:
                        result.status = "warning"
                    else:
                        result.status = "passed"

        # 生成报告
        report = health_check.generate_report(format=format, verbose=verbose)

        # 输出报告
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(report)
            click.echo(f"报告已保存到: {output}")
        else:
            click.echo(report)

        # 根据检查结果设置退出码
        if result.status == "failed":
            sys.exit(1)
        elif result.status == "warning":
            sys.exit(2)
        else:
            sys.exit(0)
    except ImportError as e:
        click.echo(f"错误: 缺少必要的依赖模块: {e}")
        sys.exit(3)
    except FileNotFoundError as e:
        click.echo(f"错误: 文件未找到: {e}")
        sys.exit(4)
    except json.JSONDecodeError as e:
        click.echo(f"错误: JSON格式错误: {e}")
        sys.exit(5)
    except Exception as e:
        click.echo(f"执行健康检查时发生错误: {e}")
        if verbose:
            click.echo(traceback.format_exc())
        sys.exit(10)


# 注册其他命令
cli.add_command(report_help)
cli.add_command(report_example)


def main():
    """入口函数"""
    cli()


if __name__ == "__main__":
    main()
