#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行入口模块

提供命令行工具的主入口，处理命令行参数并调用对应的命令处理器。
支持子命令的延迟加载，提高启动性能。
"""

import logging
import os
import sys
from importlib import import_module
from typing import Callable, Dict, Union

import click
from rich.console import Console

# 设置默认日志级别为WARNING
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()], force=True  # 强制重新配置日志
)

# 立即导入帮助命令
from src.cli.commands.help.help_click import help as help_command

logger = logging.getLogger(__name__)
console = Console()

# 命令分组（用于帮助显示）
COMMAND_GROUPS = {"基础命令": ["help", "status"], "开发工具": ["rule", "flow", "template"], "数据管理": ["db", "memory"], "项目管理": ["roadmap", "task"]}

# 子命令模块映射
COMMAND_MODULES = {
    "status": "src.cli.commands.status.status_click:status",
    "rule": "src.cli.commands.rule.rule_click:rule",
    "roadmap": "src.cli.commands.roadmap.roadmap_click:roadmap",
    "db": "src.cli.commands.db.db_click:db",
    "flow": "src.cli.commands.flow.flow_main:flow",
    "memory": "src.cli.commands.memory.memory_click:memory",
    "template": "src.cli.commands.template.template_click:template",
    "task": "src.cli.commands.task.task_click:task",
}

# 预加载的命令
PRELOADED_COMMANDS = {"help": help_command}


def load_command(module_path: str) -> click.Command:
    """
    延迟加载命令模块

    Args:
        module_path: 模块路径，格式为 "package.module:attribute"

    Returns:
        click.Command: 加载的命令对象
    """
    try:
        module_name, attribute = module_path.split(":")
        module = import_module(module_name)
        return getattr(module, attribute)
    except Exception as e:
        logger.error(f"加载命令模块失败 {module_path}: {e}")
        raise click.ClickException(f"加载命令失败: {str(e)}")


def set_log_level(verbose: bool):
    """设置全局日志级别

    Args:
        verbose: 是否启用详细日志
    """
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.getLogger().setLevel(log_level)

    if verbose:
        console.print("[dim]已启用详细日志模式[/dim]")


def print_version(ctx, param, value):
    """打印版本信息"""
    if not value or ctx.resilient_parsing:
        return
    from src import __version__

    console.print(f"[bold]VibeCopilot[/bold] version: [bold blue]{__version__}[/bold blue]")
    ctx.exit()


def initialize_status_module():
    """初始化状态模块

    此函数应该在日志级别设置后调用，确保状态模块的日志输出受CLI参数控制
    """
    try:
        logger.info("初始化状态模块...")
        # 惰性导入，确保只在需要时加载状态模块
        from src.status import initialize as init_status

        init_status()
        logger.info("状态模块初始化完成")
    except Exception as e:
        logger.error(f"状态模块初始化失败: {e}")


def get_cli_app():
    """获取CLI应用实例"""

    @click.group(help="VibeCopilot CLI工具", context_settings={"help_option_names": ["-h", "--help"]})
    @click.option("--version", is_flag=True, callback=print_version, expose_value=False, is_eager=True, help="显示版本信息")
    @click.option("--verbose", "-v", is_flag=True, help="显示详细日志信息", is_eager=True)
    @click.pass_context
    def cli(ctx, verbose):
        """VibeCopilot 命令行工具

        VibeCopilot是一个AI辅助开发工具，提供以下功能：

        1. 规则命令(/command): 由AI助手直接处理的简单交互命令
        2. 程序命令(//command): 转换为CLI执行的复杂持久化命令

        命令分组:
          基础命令:
            help     显示帮助信息
            status   项目状态管理命令

          开发工具:
            rule     规则管理命令
            flow     工作流管理命令
            template 模板管理命令

          数据管理:
            db      数据库管理命令
            memory  知识库管理命令

          项目管理:
            roadmap 路线图管理命令
            task    任务管理命令

        使用 'vc COMMAND --help' 查看具体命令的帮助信息
        """
        # 存储verbose标志在上下文中，使其对所有子命令可用
        ctx.ensure_object(dict)
        ctx.obj["VERBOSE"] = verbose

        # 设置日志级别
        set_log_level(verbose)

        # 初始化状态模块（在日志配置后执行）
        initialize_status_module()

        # 如果没有子命令，显示帮助信息
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    # 首先注册预加载的命令
    for cmd_name, cmd in PRELOADED_COMMANDS.items():
        cli.add_command(cmd)

    # 从help_click.py导入命令描述信息
    from src.cli.commands.help.help_click import COMMAND_GROUPS as HELP_COMMAND_GROUPS

    # 动态注册其他命令
    for cmd_name, module_path in COMMAND_MODULES.items():
        # 获取命令描述
        cmd_description = None
        for group in HELP_COMMAND_GROUPS.values():
            if cmd_name in group:
                cmd_description = group[cmd_name]["description"]
                break

        # 创建命令加载器
        def make_loader(mp=module_path):
            def loader():
                return load_command(mp)

            return loader

        # 创建延迟加载的命令
        cmd = click.Command(cmd_name, callback=make_loader(module_path), help=cmd_description or f"加载并执行 {cmd_name} 命令")
        cli.add_command(cmd)

    return cli


def print_error_message(command: str):
    """打印错误信息"""
    console.print(f"\n[bold red]错误:[/bold red] 未知命令: {command}")
    console.print("\n可用命令:")

    for group, commands in COMMAND_GROUPS.items():
        console.print(f"\n[bold]{group}[/bold]")
        for cmd in commands:
            console.print(f"  {cmd}")

    console.print("\n使用 [bold]vibecopilot --help[/bold] 查看详细帮助信息")


def main():
    """CLI主入口"""
    try:
        # 预准备数据库
        from src.db.connection_manager import ensure_tables_exist

        ensure_tables_exist(force_recreate=False)

        # 执行CLI命令
        cli = get_cli_app()
        cli()
        return 0  # 成功执行返回 0
    except click.exceptions.NoSuchOption as e:
        console.print(f"\n[bold red]错误:[/bold red] 无效的选项: {e.option_name}")
        console.print(f"使用 [bold]vibecopilot {e.ctx.command.name} --help[/bold] 查看有效的选项")
        return 1
    except click.exceptions.UsageError as e:
        if "No such command" in str(e):
            command = str(e).split('"')[1]
            print_error_message(command)
        else:
            console.print(f"\n[bold red]错误:[/bold red] {str(e)}")
        return 1
    except Exception as e:
        logger.exception("命令执行出错")
        console.print(f"\n[bold red]错误:[/bold red] {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
