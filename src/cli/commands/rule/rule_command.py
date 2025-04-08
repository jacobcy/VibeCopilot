#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则管理命令实现
"""

import argparse
import logging
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.cli.base_command import BaseCommand
from src.cli.command import Command
from src.cli.commands.help.help_provider import HelpProvider
from src.cli.commands.rule.core import RuleCommandExecutor, parse_rule_args
from src.cli.commands.rule.rule_command_utils import convert_result, show_help
from src.core.rule_manager import RuleManager
from src.templates.core.rule_generator import RuleGenerator
from src.templates.core.template_engine import TemplateEngine
from src.templates.core.template_manager import TemplateManager
from src.workflow.workflow_utils import get_session

logger = logging.getLogger(__name__)
console = Console()


class RuleCommand(BaseCommand, Command):
    """规则管理命令处理器"""

    def __init__(self):
        super().__init__(
            name="rule",
            description="规则管理命令",
        )
        self.template_engine = TemplateEngine()
        # 获取数据库会话并使用它初始化TemplateManager
        self.session = get_session()
        self.template_manager = TemplateManager(session=self.session)
        self.rule_generator = RuleGenerator(template_engine=self.template_engine)

        # 初始化命令执行器
        self.command_executor = RuleCommandExecutor(
            session=self.session, template_engine=self.template_engine, template_manager=self.template_manager, rule_generator=self.rule_generator
        )
        self.rule_manager = RuleManager()
        self.help_provider = HelpProvider()

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """配置命令行解析器"""
        description = """规则管理命令

用法:
  /rule <子命令> [参数]
  //rule <子命令> [参数]

子命令:
  list         列出所有规则
  show         显示规则详情
  create       创建新规则
  edit         编辑规则
  delete       删除规则
  enable       启用规则
  disable      禁用规则"""

        # 使用 RawDescriptionHelpFormatter 保留描述文本中的换行和缩进
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = description

        # 覆盖 argparse 默认的 usage 字符串
        parser.usage = "%(prog)s <子命令> [参数]"

        subparsers = parser.add_subparsers(dest="subcommand", title="可用的子命令")

        # list子命令
        list_parser = subparsers.add_parser("list", help="列出规则", description="列出所有规则或指定类型的规则")
        list_parser.add_argument("-t", "--type", help="规则类型 (core/dev/tech/tool)")

        # show子命令
        show_parser = subparsers.add_parser("show", help="显示规则详情", description="显示指定规则的详细信息")
        show_parser.add_argument("rule_name", help="规则名称")

        # create子命令
        create_parser = subparsers.add_parser("create", help="创建规则", description="创建一个新的规则")
        create_parser.add_argument("rule_name", help="规则名称")
        create_parser.add_argument("-t", "--type", required=True, help="规则类型 (core/dev/tech/tool)")
        create_parser.add_argument("-d", "--description", help="规则描述")
        create_parser.add_argument("-p", "--priority", type=int, help="规则优先级 (1-100)", choices=range(1, 101))

        # edit子命令
        edit_parser = subparsers.add_parser("edit", help="编辑规则", description="编辑现有规则")
        edit_parser.add_argument("rule_name", help="规则名称")

        # delete子命令
        delete_parser = subparsers.add_parser("delete", help="删除规则", description="删除指定的规则")
        delete_parser.add_argument("rule_name", help="规则名称")
        delete_parser.add_argument("-f", "--force", action="store_true", help="强制删除")

        # enable子命令
        enable_parser = subparsers.add_parser("enable", help="启用规则", description="启用指定的规则")
        enable_parser.add_argument("rule_name", help="规则名称")

        # disable子命令
        disable_parser = subparsers.add_parser("disable", help="禁用规则", description="禁用指定的规则")
        disable_parser.add_argument("rule_name", help="规则名称")

    def _get_command_description(self) -> str:
        """获取命令描述"""
        return """规则管理命令

用法:
  /rule <子命令> [参数]
  //rule <子命令> [参数]

子命令:
  list         列出所有规则
  show         显示规则详情
  create       创建新规则
  edit         编辑规则
  delete       删除规则
  enable       启用规则
  disable      禁用规则

选项:
  -h, --help              显示帮助信息
  -t, --type <type>       规则类型 (core/dev/tech/tool)
  -d, --desc <desc>       规则描述
  -p, --priority <num>    规则优先级 (1-100)
  -f, --force             强制执行操作

示例:
  # 列出所有规则
  /rule list
  //rule list --type core

  # 显示规则详情
  /rule show dev-rules/flow"""

    @classmethod
    def get_help(cls) -> str:
        """获取命令的帮助信息"""
        return """规则管理命令

用法:
  /rule <子命令> [参数]
  //rule <子命令> [参数]

子命令:
  list         列出所有规则
  show         显示规则详情
  create       创建新规则
  edit         编辑规则
  delete       删除规则
  enable       启用规则
  disable      禁用规则

选项:
  -h, --help              显示帮助信息
  -t, --type <type>       规则类型 (core/dev/tech/tool)
  -d, --desc <desc>       规则描述
  -p, --priority <num>    规则优先级 (1-100)
  -f, --force             强制执行操作

示例:
  # 列出所有规则
  /rule list
  //rule list --type core

  # 显示规则详情
  /rule show dev-rules/flow"""

    def execute_with_args(self, args: argparse.Namespace) -> int:
        """执行命令"""
        if not args.subcommand:
            # 直接使用Rich渲染，绕过argparse格式化问题
            from rich.markdown import Markdown

            help_md = """# 规则管理命令

## 用法
```
/rule <子命令> [参数]
//rule <子命令> [参数]
```

## 子命令
| 命令 | 描述 |
|------|------|
| `list` | 列出所有规则 |
| `show` | 显示规则详情 |
| `create` | 创建新规则 |
| `edit` | 编辑规则 |
| `delete` | 删除规则 |
| `enable` | 启用规则 |
| `disable` | 禁用规则 |

## 选项
| 选项 | 描述 |
|------|------|
| `-h, --help` | 显示帮助信息 |
| `-t, --type <type>` | 规则类型 (core/dev/tech/tool) |
| `-d, --desc <desc>` | 规则描述 |
| `-p, --priority <num>` | 规则优先级 (1-100) |
| `-f, --force` | 强制执行操作 |

## 示例
```
# 列出所有规则
/rule list
//rule list --type core

# 显示规则详情
/rule show dev-rules/flow
```
"""
            console.print(Markdown(help_md))
            return 1

        try:
            if args.subcommand == "list":
                return self._handle_list(args)
            elif args.subcommand == "show":
                return self._handle_show(args)
            elif args.subcommand == "create":
                return self._handle_create(args)
            elif args.subcommand == "edit":
                return self._handle_edit(args)
            elif args.subcommand == "delete":
                return self._handle_delete(args)
            elif args.subcommand == "enable":
                return self._handle_enable(args)
            elif args.subcommand == "disable":
                return self._handle_disable(args)
        except Exception as e:
            console.print(f"[red]错误:[/red] {str(e)}")
            return 1

        return 0

    def _handle_list(self, args: argparse.Namespace) -> int:
        table = Table(title="规则列表")
        table.add_column("名称", style="cyan")
        table.add_column("类型", style="magenta")
        table.add_column("状态", style="green")
        table.add_column("优先级", justify="right", style="yellow")
        table.add_column("描述")

        rules = self.rule_manager.list_rules(rule_type=args.type)
        for rule in rules:
            table.add_row(rule.name, rule.type, "启用" if rule.enabled else "禁用", str(rule.priority), rule.description)

        console.print(table)
        return 0

    def _handle_show(self, args: argparse.Namespace) -> int:
        rule = self.rule_manager.get_rule(args.rule_name)
        if not rule:
            console.print(f"[red]错误:[/red] 规则 '{args.rule_name}' 不存在")
            return 1

        panel = Panel(
            Markdown(rule.content),
            title=f"规则: {rule.name}",
            subtitle=f"类型: {rule.type} | 优先级: {rule.priority} | 状态: {'启用' if rule.enabled else '禁用'}",
        )
        console.print(panel)
        return 0

    def _handle_create(self, args: argparse.Namespace) -> int:
        self.rule_manager.create_rule(args.rule_name, args.type, args.description, args.priority or 50)
        console.print(f"[green]成功:[/green] 创建规则 '{args.rule_name}'")
        return 0

    def _handle_edit(self, args: argparse.Namespace) -> int:
        if not self.rule_manager.get_rule(args.rule_name):
            console.print(f"[red]错误:[/red] 规则 '{args.rule_name}' 不存在")
            return 1

        self.rule_manager.edit_rule(args.rule_name)
        console.print(f"[green]成功:[/green] 编辑规则 '{args.rule_name}'")
        return 0

    def _handle_delete(self, args: argparse.Namespace) -> int:
        if not self.rule_manager.get_rule(args.rule_name):
            console.print(f"[red]错误:[/red] 规则 '{args.rule_name}' 不存在")
            return 1

        self.rule_manager.delete_rule(args.rule_name, force=args.force)
        console.print(f"[green]成功:[/green] 删除规则 '{args.rule_name}'")
        return 0

    def _handle_enable(self, args: argparse.Namespace) -> int:
        if not self.rule_manager.get_rule(args.rule_name):
            console.print(f"[red]错误:[/red] 规则 '{args.rule_name}' 不存在")
            return 1

        self.rule_manager.enable_rule(args.rule_name)
        console.print(f"[green]成功:[/green] 启用规则 '{args.rule_name}'")
        return 0

    def _handle_disable(self, args: argparse.Namespace) -> int:
        if not self.rule_manager.get_rule(args.rule_name):
            console.print(f"[red]错误:[/red] 规则 '{args.rule_name}' 不存在")
            return 1

        self.rule_manager.disable_rule(args.rule_name)
        console.print(f"[green]成功:[/green] 禁用规则 '{args.rule_name}'")
        return 0

    def print_help(self):
        """打印帮助信息"""
        # 使用控制台直接打印格式化文本
        console.print(
            """
[bold cyan]规则管理命令[/]

[bold]用法:[/]
  /rule <子命令> [参数]
  //rule <子命令> [参数]

[bold]子命令:[/]
  [yellow]list[/]         列出所有规则
  [yellow]show[/]         显示规则详情
  [yellow]create[/]       创建新规则
  [yellow]edit[/]         编辑规则
  [yellow]delete[/]       删除规则
  [yellow]enable[/]       启用规则
  [yellow]disable[/]      禁用规则

[bold]选项:[/]
  [yellow]-h, --help[/]              显示帮助信息
  [yellow]-t, --type[/] <type>       规则类型 (core/dev/tech/tool)
  [yellow]-d, --desc[/] <desc>       规则描述
  [yellow]-p, --priority[/] <num>    规则优先级 (1-100)
  [yellow]-f, --force[/]             强制执行操作

[bold]示例:[/]
  # 列出所有规则
  [dim]/rule list[/]
  [dim]//rule list --type core[/]

  # 显示规则详情
  [dim]/rule show dev-rules/flow[/]
"""
        )
        return

    def _execute_impl(self, args: List[str]) -> int:
        """实现 Command 接口的抽象方法

        将参数转发给 execute_with_args 方法处理

        Args:
            args: 命令行参数列表

        Returns:
            命令执行结果代码
        """
        parser = argparse.ArgumentParser(prog=self.name, description=self.description)
        self.configure_parser(parser)
        parsed_args = parser.parse_args(args)
        return self.execute_with_args(parsed_args)
