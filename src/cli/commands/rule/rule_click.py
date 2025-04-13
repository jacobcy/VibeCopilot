#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则管理命令 Click 实现
"""

import logging
from typing import Optional, Tuple

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

# Assuming RuleManager and other necessary components are accessible
# Adjust imports based on actual project structure if needed
from src.core.rule_manager import RuleManager

# from src.db.connection_manager import get_session # If needed for RuleManager init

logger = logging.getLogger(__name__)
console = Console()
# Initialize RuleManager (adjust if session is needed)
# session = get_session() # Uncomment if RuleManager requires a session
# rule_manager = RuleManager(session=session) # Adjust initialization as needed
rule_manager = RuleManager()  # Assuming default init works for now


@click.group(help="规则管理命令 ")
def rule():
    """规则管理命令组"""
    pass


@rule.command(name="list", help="列出所有规则或指定类型的规则")
@click.option(
    "-t",
    "--type",
    "rule_type",
    help="规则类型 (core/dev/tech/tool)",
    required=False,
    type=click.Choice(["core", "dev", "tech", "tool"], case_sensitive=False),
)
def list_rules(rule_type: Optional[str]):
    """列出规则"""
    table = Table(title="规则列表")
    table.add_column("名称", style="cyan", no_wrap=True)
    table.add_column("类型", style="magenta")
    table.add_column("状态", style="green")
    table.add_column("优先级", justify="right", style="yellow")
    table.add_column("描述")

    try:
        rules = rule_manager.list_rules(rule_type=rule_type)
        if not rules:
            console.print(f"未找到类型为 '{rule_type}' 的规则。" if rule_type else "未找到任何规则。")
            return

        for rule_obj in rules:
            status = "启用" if rule_obj.enabled else "禁用"
            table.add_row(
                rule_obj.name,
                rule_obj.type,
                status,
                str(rule_obj.priority),
                rule_obj.description or "-",  # Handle None description
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]错误:[/red] 列出规则时出错: {e}")


@rule.command(help="显示指定规则的详细信息")
@click.argument("rule_name", type=click.STRING)
def show(rule_name: str):
    """显示规则详情"""
    try:
        rule_obj = rule_manager.get_rule(rule_name)
        if not rule_obj:
            console.print(f"[red]错误:[/red] 规则 '{rule_name}' 不存在")
            return

        status = "启用" if rule_obj.enabled else "禁用"
        panel = Panel(
            Markdown(rule_obj.content or "规则内容为空。"),  # Handle None content
            title=f"规则: {rule_obj.name}",
            subtitle=f"类型: {rule_obj.type} | 优先级: {rule_obj.priority} | 状态: {status}",
            border_style="blue",
        )
        console.print(panel)
    except Exception as e:
        console.print(f"[red]错误:[/red] 显示规则 '{rule_name}' 时出错: {e}")


@rule.command(help="创建一个新的规则")
@click.argument("rule_name", type=click.STRING)
@click.option(
    "-t",
    "--type",
    "rule_type",
    required=True,
    help="规则类型",
    type=click.Choice(["core", "dev", "tech", "tool"], case_sensitive=False),
)
@click.option("-d", "--description", help="规则描述", default=None)
@click.option(
    "-p",
    "--priority",
    type=click.IntRange(1, 100),
    help="规则优先级 (1-100)",
    default=50,
    show_default=True,
)
# Removed --content option as RuleManager.create_rule generates default content
def create(rule_name: str, rule_type: str, description: Optional[str], priority: int):
    """创建新规则"""
    try:
        # Check if rule already exists
        if rule_manager.get_rule(rule_name):
            console.print(f"[yellow]警告:[/yellow] 规则 '{rule_name}' 已存在。")
            # Optionally ask if overwrite or exit
            if not click.confirm("规则已存在，是否覆盖?"):
                return
            # If overwrite, delete first or update logic in manager needed
            # For now, let's assume create_rule handles update or we delete first
            # rule_manager.delete_rule(rule_name, force=True) # Example if delete needed

        # Call RuleManager's create_rule without content and enabled args
        # Pass description or an empty string if None
        rule_manager.create_rule(
            name=rule_name,
            rule_type=rule_type,
            description=description or "",  # Ensure str is passed
            priority=priority,
        )
        console.print(f"[green]成功:[/green] 创建规则 '{rule_name}'")
    except Exception as e:
        console.print(f"[red]错误:[/red] 创建规则 '{rule_name}' 时出错: {e}")


@rule.command(help="编辑现有规则 (在默认编辑器中打开)")
@click.argument("rule_name", type=click.STRING)
def edit(rule_name: str):
    """编辑规则"""
    try:
        rule_obj = rule_manager.get_rule(rule_name)
        if not rule_obj:
            console.print(f"[red]错误:[/red] 规则 '{rule_name}' 不存在")
            return

        # Call RuleManager's edit_rule which opens the editor directly
        rule_manager.edit_rule(rule_name)
        # No need to handle content saving here, as it's done in the external editor
        console.print(f"已在默认编辑器中打开规则 '{rule_name}' 进行编辑。请在编辑器中保存更改。")

    except Exception as e:
        console.print(f"[red]错误:[/red] 编辑规则 '{rule_name}' 时出错: {e}")


@rule.command(help="删除指定的规则")
@click.argument("rule_name", type=click.STRING)
@click.option("-f", "--force", is_flag=True, help="强制删除，无需确认")
def delete(rule_name: str, force: bool):
    """删除规则"""
    try:
        if not rule_manager.get_rule(rule_name):
            console.print(f"[red]错误:[/red] 规则 '{rule_name}' 不存在")
            return

        if force or click.confirm(f"确定要删除规则 '{rule_name}' 吗?"):
            rule_manager.delete_rule(rule_name, force=True)  # Assuming force=True bypasses internal checks if needed
            console.print(f"[green]成功:[/green] 删除规则 '{rule_name}'")
        else:
            console.print("操作已取消。")
    except Exception as e:
        console.print(f"[red]错误:[/red] 删除规则 '{rule_name}' 时出错: {e}")


@rule.command(help="启用指定的规则")
@click.argument("rule_name", type=click.STRING)
def enable(rule_name: str):
    """启用规则"""
    try:
        if not rule_manager.get_rule(rule_name):
            console.print(f"[red]错误:[/red] 规则 '{rule_name}' 不存在")
            return
        rule_manager.enable_rule(rule_name)
        console.print(f"[green]成功:[/green] 启用规则 '{rule_name}'")
    except Exception as e:
        console.print(f"[red]错误:[/red] 启用规则 '{rule_name}' 时出错: {e}")


@rule.command(help="禁用指定的规则")
@click.argument("rule_name", type=click.STRING)
def disable(rule_name: str):
    """禁用规则"""
    try:
        if not rule_manager.get_rule(rule_name):
            console.print(f"[red]错误:[/red] 规则 '{rule_name}' 不存在")
            return
        rule_manager.disable_rule(rule_name)
        console.print(f"[green]成功:[/green] 禁用规则 '{rule_name}'")
    except Exception as e:
        console.print(f"[red]错误:[/red] 禁用规则 '{rule_name}' 时出错: {e}")


# 可以添加更多命令或选项

if __name__ == "__main__":
    rule()
