#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Click版本的help命令实现
提供命令行帮助信息展示功能
"""

import logging
from typing import Dict, Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.cli.commands.help.help_provider import HelpProvider

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 创建Rich控制台实例
console = Console()

# 命令帮助信息
COMMAND_HELP: Dict[str, Dict] = {
    "rule": {
        "description": "规则管理命令",
        "subcommands": {
            "list": "列出所有规则",
            "show": "显示规则详情",
            "create": "创建新规则",
            "update": "更新规则",
            "delete": "删除规则",
            "validate": "验证规则",
            "export": "导出规则",
            "import": "导入规则",
        },
        "example": "/rule list",
    },
    "flow": {
        "description": "工作流管理命令",
        "subcommands": {
            "list": "列出所有工作流",
            "show": "查看工作流详情",
            "create": "创建工作流",
            "update": "更新工作流",
            "run": "运行工作流",
            "next": "获取下一步建议",
            "session": {"list": "列出会话", "show": "查看会话", "create": "创建会话", "pause": "暂停会话", "resume": "恢复会话"},
        },
        "example": "//flow run dev:story",
    },
    "roadmap": {
        "description": "路线图管理命令",
        "subcommands": {
            "list": "列出路线图",
            "show": "查看路线图",
            "create": "创建路线图",
            "update": "更新路线图",
            "delete": "删除路线图",
            "sync": "同步路线图",
            "switch": "切换路线图",
            "status": "查看状态",
        },
        "example": "/roadmap show",
    },
    "task": {
        "description": "任务管理命令",
        "subcommands": {"list": "列出任务", "show": "查看任务", "create": "创建任务", "update": "更新任务", "delete": "删除任务", "link": "关联任务", "comment": "添加评论"},
        "example": "//task create",
    },
    "status": {
        "description": "项目状态管理命令",
        "subcommands": {"show": "显示状态概览", "flow": "显示流程状态", "roadmap": "显示路线图状态", "task": "显示任务状态", "update": "更新项目阶段", "init": "初始化状态"},
        "example": "/status show",
    },
    "memory": {
        "description": "知识库管理命令",
        "subcommands": {
            "list": "列出内容",
            "show": "显示详情",
            "create": "创建内容",
            "update": "更新内容",
            "delete": "删除内容",
            "search": "搜索内容",
            "import": "导入内容",
            "export": "导出内容",
            "sync": "同步内容",
        },
        "example": "/memory search",
    },
    "db": {
        "description": "数据库管理命令",
        "subcommands": {
            "init": "初始化数据库",
            "list": "列出内容",
            "show": "显示详情",
            "create": "创建条目",
            "update": "更新条目",
            "delete": "删除条目",
            "query": "查询数据",
            "backup": "备份数据库",
            "restore": "恢复数据库",
        },
        "example": "//db init",
    },
    "template": {
        "description": "模板管理命令",
        "subcommands": {
            "list": "列出模板",
            "show": "查看模板",
            "create": "创建模板",
            "update": "更新模板",
            "delete": "删除模板",
            "import": "导入模板",
            "export": "导出模板",
            "generate": "生成文件",
            "init": "初始化",
        },
        "example": "/template list",
    },
}


@click.group(help="显示帮助信息")
def help():
    """VibeCopilot帮助命令组"""
    pass


@help.command(name="show")
@click.argument("command", required=False)
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def show_help(command: Optional[str] = None, verbose: bool = False):
    """
    显示命令帮助信息

    Args:
        command: 要查看帮助的具体命令
        verbose: 是否显示详细信息
    """
    try:
        help_provider = HelpProvider()

        if command:
            # 显示特定命令的帮助信息
            command_help = COMMAND_HELP.get(command) or help_provider.get_command_help(command)
            if command_help:
                _display_command_help(command, command_help, verbose)
            else:
                console.print(f"[red]错误: 未找到命令 '{command}' 的帮助信息[/red]")
        else:
            # 显示通用帮助信息
            _display_general_help(help_provider, verbose)

    except Exception as e:
        logger.error(f"显示帮助信息时发生错误: {str(e)}")
        console.print(f"[red]错误: {str(e)}[/red]")
        if verbose:
            import traceback

            console.print("[yellow]详细错误信息:[/yellow]")
            console.print(traceback.format_exc())


def _display_general_help(help_provider: HelpProvider, verbose: bool = False):
    """显示通用帮助信息"""
    # 创建标题面板
    title_panel = Panel("[bold cyan]VibeCopilot[/bold cyan] [white]命令行工具[/white]", subtitle="输入命令获取帮助")
    console.print(title_panel)

    # 显示命令类型说明
    console.print("\n[bold]命令类型说明:[/bold]")
    types_table = Table(show_header=False, box=None, padding=(0, 2))
    types_table.add_column("Type", style="cyan")
    types_table.add_column("Description")
    types_table.add_row("/command", "规则命令 - 由AI直接处理的简单交互命令")
    types_table.add_row("//command", "程序命令 - 转换为CLI执行的复杂持久化命令")
    console.print(types_table)

    # 创建命令表格
    console.print("\n[bold]可用命令:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("命令", style="cyan")
    table.add_column("描述")
    table.add_column("示例", style="green")

    # 添加所有命令
    for cmd_name, cmd_info in COMMAND_HELP.items():
        table.add_row(cmd_name, cmd_info["description"], cmd_info["example"])

    console.print(table)

    # 显示基本用法
    console.print("\n[bold]基本用法:[/bold]")
    usage_md = """
```bash
# 查看命令帮助
/help [命令]
//help [命令] --verbose

# 规则命令示例
/rule list
/task create "新任务"
/memory search "架构设计"

# 程序命令示例
//flow run dev:story
//roadmap create --name="2023计划"
//db init
```
"""
    console.print(Markdown(usage_md))

    if verbose:
        # 显示通用选项
        console.print("\n[bold]通用选项:[/bold]")
        options_table = Table(show_header=False, box=None, padding=(0, 2))
        options_table.add_column("Option", style="yellow")
        options_table.add_column("Description")
        options_table.add_row("--verbose", "显示详细信息")
        options_table.add_row("--format=<json|text>", "指定输出格式")
        console.print(options_table)

        # 显示提示信息
        console.print("\n[bold]提示:[/bold]")
        tips_md = """
- 使用 `/help <命令>` 获取特定命令的详细帮助
- 使用 `--verbose` 参数获取更多信息
- 规则命令(/)用于简单交互，程序命令(//)用于复杂操作
- 所有命令支持 `--help` 参数显示帮助
"""
        console.print(Markdown(tips_md))


def _display_command_help(command: str, help_info: dict, verbose: bool = False):
    """显示特定命令的帮助信息"""
    # 创建命令标题
    title = Text()
    title.append(f"命令: ", style="bold blue")
    title.append(command, style="bold cyan")

    console.print("\n" + str(title))

    # 显示基本信息
    if "description" in help_info:
        console.print(f"\n[bold]描述:[/bold]\n{help_info['description']}")

    # 显示子命令
    if "subcommands" in help_info:
        console.print("\n[bold]子命令:[/bold]")
        subtable = Table(show_header=True, header_style="bold magenta")
        subtable.add_column("子命令", style="cyan")
        subtable.add_column("描述")

        for subcmd, subcmd_info in help_info["subcommands"].items():
            if isinstance(subcmd_info, dict):
                # 处理嵌套子命令
                for nested_cmd, nested_desc in subcmd_info.items():
                    subtable.add_row(f"{subcmd} {nested_cmd}", nested_desc)
            else:
                subtable.add_row(subcmd, subcmd_info)

        console.print(subtable)

    # 显示示例
    if "example" in help_info:
        console.print("\n[bold]示例:[/bold]")
        console.print(f"  {help_info['example']}")

    if verbose:
        # 显示详细选项
        console.print("\n[bold]通用选项:[/bold]")
        options_table = Table(show_header=False, box=None, padding=(0, 2))
        options_table.add_column("Option", style="yellow")
        options_table.add_column("Description")
        options_table.add_row("--verbose", "显示详细信息")
        options_table.add_row("--format=<json|text>", "指定输出格式")
        console.print(options_table)


if __name__ == "__main__":
    help()
