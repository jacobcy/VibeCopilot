#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则管理命令 Click 实现
"""

import logging
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.rule_engine import RuleManager, init_rule_engine
from src.validation.rule_validator import validate_rule

logger = logging.getLogger(__name__)
console = Console()
rule_manager = init_rule_engine()


@click.group(help="规则管理命令")
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
@click.option(
    "-f",
    "--format",
    "output_format",
    help="输出格式",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
)
def list_rules(rule_type: Optional[str], output_format: str):
    """列出规则"""
    try:
        rules = rule_manager.list_rules(rule_type=rule_type)
        if not rules:
            console.print(f"未找到类型为 '{rule_type}' 的规则。" if rule_type else "未找到任何规则。")
            return

        if output_format == "table":
            table = Table(title="规则列表")
            table.add_column("名称", style="cyan", no_wrap=True)
            table.add_column("类型", style="magenta")
            table.add_column("优先级", justify="right", style="yellow")
            table.add_column("描述")

            for rule in rules:
                table.add_row(
                    rule.id,
                    rule.type,
                    str(rule.priority),
                    rule.description or "-",
                )
            console.print(table)
        else:
            # 导出为其他格式
            data = [{"id": r.id, "type": r.type, "priority": r.priority, "description": r.description} for r in rules]
            if output_format == "json":
                import json

                console.print(json.dumps(data, indent=2, ensure_ascii=False))
            elif output_format == "yaml":
                import yaml

                console.print(yaml.dump(data, allow_unicode=True))
    except Exception as e:
        console.print(f"[red]错误:[/red] 列出规则时出错: {e}")


@rule.command(help="显示指定规则的详细信息")
@click.argument("rule_name", type=click.STRING)
@click.option(
    "-f",
    "--format",
    "output_format",
    help="输出格式",
    type=click.Choice(["markdown", "json", "yaml"]),
    default="markdown",
)
def show(rule_name: str, output_format: str):
    """显示规则详情"""
    try:
        rule = rule_manager.get_rule(rule_name)
        if not rule:
            console.print(f"[red]错误:[/red] 规则 '{rule_name}' 不存在")
            return

        if output_format == "markdown":
            panel = Panel(
                Markdown(rule.content or "规则内容为空。"),
                title=f"规则: {rule.id}",
                subtitle=f"类型: {rule.type} | 优先级: {rule.priority}",
                border_style="blue",
            )
            console.print(panel)
        else:
            # 导出为其他格式
            data = rule.dict()
            if output_format == "json":
                import json

                console.print(json.dumps(data, indent=2, ensure_ascii=False))
            elif output_format == "yaml":
                import yaml

                console.print(yaml.dump(data, allow_unicode=True))
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
def create(rule_name: str, rule_type: str, description: Optional[str], priority: int):
    """创建新规则"""
    try:
        # 生成规则内容
        content = f"""---
type: {rule_type}
description: {description or ''}
priority: {priority}
---

# {rule_name}

{description or ''}

## 使用场景

## 规则内容

## 示例
"""
        # 导入规则内容
        rule = rule_manager.import_rule_from_content(content=content, context=f"创建规则 {rule_name}", validate=True, overwrite=True)
        console.print(f"[green]成功:[/green] 创建规则 '{rule_name}'")
    except Exception as e:
        console.print(f"[red]错误:[/red] 创建规则 '{rule_name}' 时出错: {e}")


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
            if rule_manager.delete_rule(rule_name):
                console.print(f"[green]成功:[/green] 删除规则 '{rule_name}'")
            else:
                console.print(f"[red]错误:[/red] 删除规则 '{rule_name}' 失败")
        else:
            console.print("操作已取消。")
    except Exception as e:
        console.print(f"[red]错误:[/red] 删除规则 '{rule_name}' 时出错: {e}")


@rule.command(name="import", help="从文件导入规则")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--parser", help="解析器类型", type=str)
@click.option("--model", help="模型名称", type=str)
@click.option("--validate/--no-validate", help="是否验证规则", default=True)
@click.option("--overwrite/--no-overwrite", help="是否覆盖已存在的规则", default=False)
def import_(file_path: str, parser: Optional[str], model: Optional[str], validate: bool, overwrite: bool):
    """从文件导入规则"""
    try:
        rule = rule_manager.import_rule(file_path)
        console.print(f"[green]成功:[/green] 导入规则 '{rule.id}'")
    except Exception as e:
        console.print(f"[red]错误:[/red] 导入规则时出错: {e}")


@rule.command(name="export", help="导出规则")
@click.argument("rule_name", type=click.STRING)
@click.option(
    "-f",
    "--format",
    "format_type",
    help="导出格式",
    type=click.Choice(["yaml", "json", "markdown"]),
    default="yaml",
)
@click.option("-o", "--output", help="输出路径", type=click.Path())
def export_(rule_name: str, format_type: str, output: Optional[str]):
    """导出规则"""
    try:
        content = rule_manager.export_rule(rule_name, format_type)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            console.print(f"[green]成功:[/green] 规则已导出到 '{output}'")
        else:
            console.print(content)
    except Exception as e:
        console.print(f"[red]错误:[/red] 导出规则 '{rule_name}' 时出错: {e}")


@rule.command(help="验证规则")
@click.argument("rule_name", type=click.STRING)
def validate(rule_name: str):
    """验证规则"""
    try:
        rule = rule_manager.get_rule(rule_name)
        if not rule:
            console.print(f"[red]错误:[/red] 规则 '{rule_name}' 不存在")
            return

        result = validate_rule(rule)
        if result:
            console.print(f"[green]成功:[/green] 规则 '{rule_name}' 验证通过")
        else:
            console.print(f"[red]错误:[/red] 规则 '{rule_name}' 验证失败")
    except Exception as e:
        console.print(f"[red]错误:[/red] 验证规则时出错: {e}")


if __name__ == "__main__":
    rule()
