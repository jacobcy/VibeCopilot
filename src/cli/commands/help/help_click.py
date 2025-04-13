#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Click版本的help命令实现
提供命令行帮助信息展示功能
"""

import logging
from typing import Dict, Optional

import click

from src.cli.commands.help.help_provider import HelpProvider

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

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

# 命令分组信息
COMMAND_GROUPS = {
    "基础命令": {"help": {"description": "显示帮助信息", "example": "/help [命令]"}, "status": {"description": "项目状态管理命令", "example": "/status show"}},
    "开发工具": {
        "rule": {"description": "规则管理命令", "example": "/rule list"},
        "flow": {"description": "工作流管理命令", "example": "//flow run dev:story"},
        "template": {"description": "模板管理命令", "example": "/template list"},
    },
    "数据管理": {"db": {"description": "数据库管理命令", "example": "//db init"}, "memory": {"description": "知识库管理命令", "example": "/memory search"}},
    "项目管理": {"roadmap": {"description": "路线图管理命令", "example": "/roadmap show"}, "task": {"description": "任务管理命令", "example": "//task create"}},
}


def format_help_text():
    """
    生成通用帮助文本
    """
    help_text = [
        "用法: vc [OPTIONS] COMMAND [ARGS]...",
        "",
        "VibeCopilot命令行工具",
        "",
        "命令组:",
    ]

    # 添加命令组信息
    for group_name, commands in COMMAND_GROUPS.items():
        help_text.append(f"\n  {group_name}:")
        for cmd_name, cmd_info in commands.items():
            # 对齐处理：命令名占12个字符宽度
            help_text.append(f"    {cmd_name:<12} {cmd_info['description']}")

    help_text.extend(
        [
            "",
            "通用选项:",
            "  -h, --help     显示帮助信息",
            "  -v, --verbose  显示详细信息",
            "  --version      显示版本信息",
            "",
            "命令类型:",
            "  /command       规则命令 - 由AI直接处理的简单交互命令",
            "  //command      程序命令 - 转换为CLI执行的复杂持久化命令",
            "",
            "使用示例:",
            "  vc --help              显示此帮助信息",
            "  vc COMMAND --help      显示具体命令的帮助",
            "  vc help show COMMAND   显示命令的详细帮助",
        ]
    )

    return "\n".join(help_text)


def format_command_help(command: str, help_info: dict, verbose: bool = False):
    """
    生成特定命令的帮助文本
    """
    help_text = [f"用法: vc {command} [OPTIONS] [ARGS]...", "", help_info.get("description", "未提供描述"), "", "子命令:"]

    if "subcommands" in help_info:
        for subcmd, subcmd_info in help_info["subcommands"].items():
            if isinstance(subcmd_info, dict):
                for nested_cmd, nested_desc in subcmd_info.items():
                    # 对齐处理：子命令名占20个字符宽度
                    help_text.append(f"  {subcmd} {nested_cmd:<20} {nested_desc}")
            else:
                # 对齐处理：命令名占20个字符宽度
                help_text.append(f"  {subcmd:<20} {subcmd_info}")

    help_text.extend(
        [
            "",
            "选项:",
            "  -h, --help            显示此帮助信息",
            "  -v, --verbose         显示详细信息",
        ]
    )

    if verbose:
        help_text.extend(["  --format=<json|text>  指定输出格式", "", "详细说明:", "  - 此命令支持详细模式，使用 --verbose 查看更多信息", "  - 支持JSON输出格式，使用 --format=json 指定"])

    help_text.extend(["", "示例:", f"  {help_info.get('example', '未提供示例')}"])

    return "\n".join(help_text)


@click.group(help="显示帮助信息", invoke_without_command=True)
@click.pass_context
def help(ctx):
    """VibeCopilot帮助命令组"""
    if ctx.invoked_subcommand is None:
        click.echo(format_help_text())


@help.command(name="show")
@click.argument("command", required=False)
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def show_help(command: Optional[str] = None, verbose: bool = False):
    """显示命令帮助信息"""
    try:
        help_provider = HelpProvider()

        if command:
            command_help = COMMAND_HELP.get(command) or help_provider.get_command_help(command)
            if command_help:
                click.echo(format_command_help(command, command_help, verbose))
            else:
                click.echo(f"错误: 未找到命令 '{command}' 的帮助信息")
        else:
            click.echo(format_help_text())

    except Exception as e:
        logger.error(f"显示帮助信息时发生错误: {str(e)}")
        click.echo(f"错误: {str(e)}")
        if verbose:
            import traceback

            click.echo("详细错误信息:")
            click.echo(traceback.format_exc())


if __name__ == "__main__":
    help()
