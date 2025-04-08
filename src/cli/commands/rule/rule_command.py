#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则管理命令实现
"""

import argparse
import logging
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.cli.base_command import BaseCommand
from src.cli.command import Command
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

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """配置命令行解析器"""
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = self._get_command_description()

        subparsers = parser.add_subparsers(dest="subcommand", help="子命令")

        # list子命令
        list_parser = subparsers.add_parser("list", help="列出规则")
        list_parser.add_argument("-t", "--type", help="规则类型")

        # show子命令
        show_parser = subparsers.add_parser("show", help="显示规则详情")
        show_parser.add_argument("rule_name", help="规则名称")

        # create子命令
        create_parser = subparsers.add_parser("create", help="创建规则")
        create_parser.add_argument("rule_name", help="规则名称")
        create_parser.add_argument("-t", "--type", required=True, help="规则类型")
        create_parser.add_argument("-d", "--description", help="规则描述")
        create_parser.add_argument("-p", "--priority", type=int, help="规则优先级 (1-100)", choices=range(1, 101))

        # edit子命令
        edit_parser = subparsers.add_parser("edit", help="编辑规则")
        edit_parser.add_argument("rule_name", help="规则名称")

        # delete子命令
        delete_parser = subparsers.add_parser("delete", help="删除规则")
        delete_parser.add_argument("rule_name", help="规则名称")
        delete_parser.add_argument("-f", "--force", action="store_true", help="强制删除")

        # enable子命令
        enable_parser = subparsers.add_parser("enable", help="启用规则")
        enable_parser.add_argument("rule_name", help="规则名称")

        # disable子命令
        disable_parser = subparsers.add_parser("disable", help="禁用规则")
        disable_parser.add_argument("rule_name", help="规则名称")

    def _get_command_description(self) -> str:
        """获取命令描述"""
        return """规则管理命令

用法:
    vc rule list                     # 列出所有规则
    vc rule show <rule_name>         # 显示规则详情
    vc rule create <rule_name>       # 创建新规则
    vc rule edit <rule_name>         # 编辑规则
    vc rule delete <rule_name>       # 删除规则
    vc rule enable <rule_name>       # 启用规则
    vc rule disable <rule_name>      # 禁用规则

参数:
    rule_name                        规则名称

选项:
    -h, --help                       显示帮助信息
    -t, --type <type>               规则类型 (core/dev/tech/tool)
    -d, --description <desc>         规则描述
    -p, --priority <num>            规则优先级 (1-100)
    -f, --force                     强制执行操作
"""

    def execute_with_args(self, args: argparse.Namespace) -> int:
        """执行命令"""
        if not args.subcommand:
            self.print_help()
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


@click.group()
def rule():
    """规则管理命令

    用法:
        rule list                                    列出所有规则
        rule list [--type=<rule_type>] [--verbose]  列出特定类型的规则
        rule show <id> [--format=<json|text>]       显示规则详情
        rule create <template_type> <name> [--vars=<json>]  创建新规则
        rule update <id> [--vars=<json>]            更新规则
        rule delete <id> [--force]                  删除规则
        rule validate <id> [--all]                  验证规则
        rule export <id> [--output=<path>] [--format=<format>]  导出规则
        rule import <file_path> [--overwrite]       导入规则

    参数:
        <id>                  规则ID
        <template_type>       模板类型
        <name>               规则名称
        <file_path>          规则文件路径

    选项:
        --type=<rule_type>    规则类型
        --format=<format>     输出格式(json或text)
        --vars=<json>         变量值（JSON格式）
        --output=<path>       输出路径
        --force              强制执行危险操作
        --verbose            显示详细信息
        --all                处理所有规则
        --overwrite          覆盖已存在的规则
    """
    pass
