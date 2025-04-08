#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帮助命令实现

提供命令行帮助信息，支持规则命令和程序命令
"""

import argparse
import logging
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.cli.commands.base_command import BaseCommand

logger = logging.getLogger(__name__)
console = Console()


class HelpCommand(BaseCommand):
    """帮助命令"""

    def __init__(self):
        super().__init__(
            name="help",
            description="显示帮助信息",
        )

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """配置命令行解析器"""
        parser.add_argument("command", nargs="?", help="要查看帮助的命令")
        parser.add_argument("--verbose", action="store_true", help="显示详细信息")

    def execute_with_args(self, args: argparse.Namespace) -> int:
        """执行命令"""
        if hasattr(args, "command") and args.command:
            return self._show_command_help(args.command, args.verbose)
        else:
            return self._show_general_help(args.verbose)

    def _show_general_help(self, verbose: bool = False) -> int:
        """显示通用帮助信息"""
        # 显示标题
        console.print(Panel.fit("[bold cyan]VibeCopilot[/bold cyan] [white]命令行工具[/white]", subtitle="输入命令获取帮助"))

        # 显示命令类型说明
        console.print("\n[bold]命令类型说明:[/bold]")
        types_table = Table(show_header=False, box=None, padding=(0, 2))
        types_table.add_column("Type", style="cyan")
        types_table.add_column("Description")
        types_table.add_row("/command", "规则命令 - 由AI直接处理的简单交互命令")
        types_table.add_row("//command", "程序命令 - 转换为CLI执行的复杂持久化命令")
        console.print(types_table)

        # 显示可用命令
        console.print("\n[bold]可用命令:[/bold]")
        commands_table = Table(show_header=True, box=None, padding=(0, 2))
        commands_table.add_column("命令", style="cyan")
        commands_table.add_column("说明")
        commands_table.add_column("示例", style="green")

        commands = [
            ("help", "显示帮助信息", "/help flow"),
            ("rule", "规则管理命令", "/rule list"),
            ("flow", "工作流管理命令", "//flow run dev:story"),
            ("roadmap", "路线图管理命令", "/roadmap show"),
            ("task", "任务管理命令", "//task create"),
            ("status", "项目状态管理命令", "/status show"),
            ("memory", "知识库管理命令", "/memory search"),
            ("db", "数据库管理命令", "//db init"),
            ("template", "模板管理命令", "/template list"),
        ]

        for cmd, desc, example in commands:
            commands_table.add_row(cmd, desc, example)

        console.print(commands_table)

        # 显示用法说明
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
            # 显示详细选项
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

        return 0

    def _show_command_help(self, command_name: str, verbose: bool = False) -> int:
        """显示特定命令的帮助信息"""
        # 创建命令帮助面板
        title = f"[bold cyan]{command_name}[/bold cyan] 命令帮助"

        if command_name == "help":
            content = self._get_help_command_help(verbose)
        elif command_name == "rule":
            content = self._get_rule_command_help(verbose)
        elif command_name == "flow":
            content = self._get_flow_command_help(verbose)
        elif command_name == "roadmap":
            content = self._get_roadmap_command_help(verbose)
        elif command_name == "task":
            content = self._get_task_command_help(verbose)
        elif command_name == "status":
            content = self._get_status_command_help(verbose)
        elif command_name == "memory":
            content = self._get_memory_command_help(verbose)
        elif command_name == "db":
            content = self._get_db_command_help(verbose)
        elif command_name == "template":
            content = self._get_template_command_help(verbose)
        else:
            logger.error(f"未知命令: {command_name}")
            console.print(f"[red]错误:[/red] 未知命令 '{command_name}'")
            console.print("\n[yellow]提示:[/yellow] 使用 [cyan]/help[/cyan] 查看所有可用命令")
            return 1

        # 显示命令帮助
        console.print(Panel(content, title=title))

        # 显示通用选项
        if verbose:
            console.print("\n[bold]通用选项:[/bold]")
            options_table = Table(show_header=False, box=None, padding=(0, 2))
            options_table.add_column("Option", style="yellow")
            options_table.add_column("Description")
            options_table.add_row("--verbose", "显示详细信息")
            options_table.add_row("--format=<json|text>", "指定输出格式")
            console.print(options_table)

        return 0

    def _get_help_command_help(self, verbose: bool = False) -> str:
        """获取help命令的帮助信息"""
        return """
[bold]用法:[/bold]
```bash
/help [命令] [--verbose]
//help [命令] [--verbose]
```

[bold]参数:[/bold]
[yellow]命令[/yellow]        要查看帮助的命令名称
[yellow]--verbose[/yellow]   显示详细信息

[bold]示例:[/bold]
```bash
/help                # 显示所有命令
/help flow          # 显示flow命令帮助
//help --verbose    # 显示详细帮助信息
```
"""

    def _get_rule_command_help(self, verbose: bool = False) -> str:
        """获取rule命令的帮助信息"""
        base_help = """
[bold]用法:[/bold]
```bash
/rule <子命令> [参数]
//rule <子命令> [参数]
```

[bold]子命令:[/bold]
[cyan]list[/cyan]     列出所有规则
[cyan]show[/cyan]     显示规则详情
[cyan]create[/cyan]   创建新规则
[cyan]update[/cyan]   更新规则
[cyan]delete[/cyan]   删除规则
[cyan]validate[/cyan] 验证规则
[cyan]export[/cyan]   导出规则
[cyan]import[/cyan]   导入规则
"""
        if verbose:
            base_help += """
[bold]示例:[/bold]
```bash
/rule list                          # 列出所有规则
/rule show <id>                     # 显示规则详情
//rule create <template> <name>     # 创建新规则
//rule update <id> --vars=<json>    # 更新规则
//rule delete <id> --force          # 删除规则
//rule validate --all               # 验证所有规则
//rule export --output=rules.json   # 导出规则
//rule import rules.json            # 导入规则
```

[bold]参数说明:[/bold]
[yellow]<id>[/yellow]                规则ID
[yellow]<template>[/yellow]          模板类型
[yellow]<name>[/yellow]              规则名称
[yellow]--type=<type>[/yellow]       规则类型
[yellow]--format=<format>[/yellow]   输出格式
[yellow]--vars=<json>[/yellow]       变量值
[yellow]--output=<path>[/yellow]     输出路径
[yellow]--force[/yellow]             强制执行
[yellow]--all[/yellow]               处理所有规则
"""
        return base_help

    def _get_flow_command_help(self, verbose: bool = False) -> str:
        """获取flow命令的帮助信息"""
        base_help = """
[bold]用法:[/bold]
```bash
/flow <子命令> [参数]
//flow <子命令> [参数]
```

[bold]工作流定义子命令:[/bold]
[cyan]list[/cyan]      列出所有工作流
[cyan]show[/cyan]      查看工作流详情
[cyan]create[/cyan]    创建工作流
[cyan]update[/cyan]    更新工作流
[cyan]run[/cyan]       运行工作流
[cyan]next[/cyan]      获取下一步建议

[bold]工作流会话子命令:[/bold]
[cyan]session list[/cyan]    列出会话
[cyan]session show[/cyan]    查看会话
[cyan]session create[/cyan]  创建会话
[cyan]session pause[/cyan]   暂停会话
[cyan]session resume[/cyan]  恢复会话
"""
        if verbose:
            base_help += """
[bold]示例:[/bold]
```bash
/flow list                              # 列出工作流
/flow show dev:story                    # 查看工作流
//flow run dev:story --name="登录功能"   # 运行工作流
/flow next                              # 获取建议
//flow session list                     # 列出会话
//flow session pause <id>               # 暂停会话
```

[bold]参数说明:[/bold]
[yellow]--type=<type>[/yellow]         工作流类型
[yellow]--name=<name>[/yellow]         工作流名称
[yellow]--session=<id>[/yellow]        会话ID
[yellow]--format=<format>[/yellow]     输出格式
"""
        return base_help

    def _get_roadmap_command_help(self, verbose: bool = False) -> str:
        """获取roadmap命令的帮助信息"""
        base_help = """
[bold]用法:[/bold]
```bash
/roadmap <子命令> [参数]
//roadmap <子命令> [参数]
```

[bold]子命令:[/bold]
[cyan]list[/cyan]     列出路线图
[cyan]show[/cyan]     查看路线图
[cyan]create[/cyan]   创建路线图
[cyan]update[/cyan]   更新路线图
[cyan]delete[/cyan]   删除路线图
[cyan]sync[/cyan]     同步路线图
[cyan]switch[/cyan]   切换路线图
[cyan]status[/cyan]   查看状态
"""
        if verbose:
            base_help += """
[bold]示例:[/bold]
```bash
/roadmap list                    # 列出路线图
/roadmap show <id>              # 查看路线图
//roadmap create --name="2024"  # 创建路线图
//roadmap update <id>           # 更新路线图
//roadmap sync github           # 同步GitHub
//roadmap switch <id>           # 切换路线图
```

[bold]参数说明:[/bold]
[yellow]--name=<name>[/yellow]         路线图名称
[yellow]--desc=<desc>[/yellow]         路线图描述
[yellow]--source=<source>[/yellow]     同步数据源
[yellow]--format=<format>[/yellow]     输出格式
"""
        return base_help

    def _get_task_command_help(self, verbose: bool = False) -> str:
        """获取task命令的帮助信息"""
        base_help = """
[bold]用法:[/bold]
```bash
/task <子命令> [参数]
//task <子命令> [参数]
```

[bold]子命令:[/bold]
[cyan]list[/cyan]     列出任务
[cyan]show[/cyan]     查看任务
[cyan]create[/cyan]   创建任务
[cyan]update[/cyan]   更新任务
[cyan]delete[/cyan]   删除任务
[cyan]link[/cyan]     关联任务
[cyan]comment[/cyan]  添加评论
"""
        if verbose:
            base_help += """
[bold]示例:[/bold]
```bash
/task list                           # 列出任务
/task show <id>                      # 查看任务
//task create --title="新功能"        # 创建任务
//task update <id> --status="done"   # 更新任务
//task link <id> --to=<target>       # 关联任务
//task comment <id> "评论内容"        # 添加评论
```

[bold]参数说明:[/bold]
[yellow]--title=<title>[/yellow]         任务标题
[yellow]--desc=<desc>[/yellow]           任务描述
[yellow]--assignee=<user>[/yellow]       负责人
[yellow]--status=<status>[/yellow]       任务状态
[yellow]--format=<format>[/yellow]       输出格式
"""
        return base_help

    def _get_status_command_help(self, verbose: bool = False) -> str:
        """获取status命令的帮助信息"""
        base_help = """
[bold]用法:[/bold]
```bash
/status <子命令> [参数]
//status <子命令> [参数]
```

[bold]子命令:[/bold]
[cyan]show[/cyan]     显示状态概览
[cyan]flow[/cyan]     显示流程状态
[cyan]roadmap[/cyan]  显示路线图状态
[cyan]task[/cyan]     显示任务状态
[cyan]update[/cyan]   更新项目阶段
[cyan]init[/cyan]     初始化状态
"""
        if verbose:
            base_help += """
[bold]示例:[/bold]
```bash
/status show                    # 显示概览
/status flow                    # 显示流程
//status roadmap               # 显示路线图
//status task                 # 显示任务
//status update --phase="dev"  # 更新阶段
//status init                 # 初始化
```

[bold]参数说明:[/bold]
[yellow]--type=<type>[/yellow]         状态类型
[yellow]--phase=<phase>[/yellow]       项目阶段
[yellow]--name=<name>[/yellow]         项目名称
"""
        return base_help

    def _get_memory_command_help(self, verbose: bool = False) -> str:
        """获取memory命令的帮助信息"""
        base_help = """
[bold]用法:[/bold]
```bash
/memory <子命令> [参数]
//memory <子命令> [参数]
```

[bold]子命令:[/bold]
[cyan]list[/cyan]     列出内容
[cyan]show[/cyan]     显示详情
[cyan]create[/cyan]   创建内容
[cyan]update[/cyan]   更新内容
[cyan]delete[/cyan]   删除内容
[cyan]search[/cyan]   搜索内容
[cyan]import[/cyan]   导入内容
[cyan]export[/cyan]   导出内容
[cyan]sync[/cyan]     同步内容
"""
        if verbose:
            base_help += """
[bold]示例:[/bold]
```bash
/memory list                          # 列出内容
/memory show <id>                     # 显示详情
//memory create --title="架构设计"     # 创建内容
//memory search "性能优化"            # 搜索内容
//memory import ./docs               # 导入文档
//memory export --format=markdown    # 导出内容
```

[bold]参数说明:[/bold]
[yellow]--title=<title>[/yellow]         内容标题
[yellow]--folder=<folder>[/yellow]       存储目录
[yellow]--query=<query>[/yellow]         搜索查询
[yellow]--format=<format>[/yellow]       输出格式
"""
        return base_help

    def _get_db_command_help(self, verbose: bool = False) -> str:
        """获取db命令的帮助信息"""
        base_help = """
[bold]用法:[/bold]
```bash
/db <子命令> [参数]
//db <子命令> [参数]
```

[bold]子命令:[/bold]
[cyan]init[/cyan]     初始化数据库
[cyan]list[/cyan]     列出内容
[cyan]show[/cyan]     显示详情
[cyan]create[/cyan]   创建条目
[cyan]update[/cyan]   更新条目
[cyan]delete[/cyan]   删除条目
[cyan]query[/cyan]    查询数据
[cyan]backup[/cyan]   备份数据库
[cyan]restore[/cyan]  恢复数据库
"""
        if verbose:
            base_help += """
[bold]示例:[/bold]
```bash
//db init                           # 初始化
/db list --type=rule               # 列出规则
/db show <id>                      # 显示详情
//db create --data='{"key":"val"}' # 创建条目
//db backup                        # 备份数据
//db restore backup.sql            # 恢复数据
```

[bold]参数说明:[/bold]
[yellow]--type=<type>[/yellow]         实体类型
[yellow]--id=<id>[/yellow]             条目ID
[yellow]--data=<json>[/yellow]         数据内容
[yellow]--format=<format>[/yellow]     输出格式
"""
        return base_help

    def _get_template_command_help(self, verbose: bool = False) -> str:
        """获取template命令的帮助信息"""
        base_help = """
[bold]用法:[/bold]
```bash
/template <子命令> [参数]
//template <子命令> [参数]
```

[bold]子命令:[/bold]
[cyan]list[/cyan]     列出模板
[cyan]show[/cyan]     查看模板
[cyan]create[/cyan]   创建模板
[cyan]update[/cyan]   更新模板
[cyan]delete[/cyan]   删除模板
[cyan]import[/cyan]   导入模板
[cyan]export[/cyan]   导出模板
[cyan]generate[/cyan] 生成文件
[cyan]init[/cyan]     初始化
"""
        if verbose:
            base_help += """
[bold]示例:[/bold]
```bash
/template list                    # 列出模板
/template show <id>              # 查看模板
//template create --name="api"   # 创建模板
//template generate <id>         # 生成文件
//template import ./templates    # 导入模板
//template init                 # 初始化
```

[bold]参数说明:[/bold]
[yellow]--name=<name>[/yellow]         模板名称
[yellow]--type=<type>[/yellow]         模板类型
[yellow]--content=<content>[/yellow]   模板内容
[yellow]--vars=<json>[/yellow]         模板变量
[yellow]--format=<format>[/yellow]     输出格式
"""
        return base_help
