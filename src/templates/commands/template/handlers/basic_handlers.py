"""
基本模板命令处理模块

提供模板的基本操作，如列表查看、详情查看和删除
"""

import argparse
import json
import logging
from typing import List

from rich.console import Console
from rich.table import Table

from src.db import get_session_factory
from src.models.template import Template
from src.templates.core.template_manager import TemplateManager

logger = logging.getLogger(__name__)
console = Console()


def handle_template_list(args: argparse.Namespace) -> None:
    """
    处理模板列表命令

    Args:
        args: 命令行参数
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 获取模板列表
        if hasattr(args, "template_type") and args.template_type:
            templates = template_manager.get_templates_by_type(args.template_type)
        elif hasattr(args, "tags") and args.tags:
            templates = template_manager.search_templates(tags=args.tags)
        else:
            templates = template_manager.get_all_templates()

        # 设置默认格式
        output_format = "table"
        if hasattr(args, "format"):
            output_format = args.format

        # 根据格式输出
        if output_format == "json":
            # JSON格式
            templates_data = [
                {
                    "id": t.id,
                    "name": t.name,
                    "type": t.type,
                    "description": t.description,
                }
                for t in templates
            ]
            console.print(json.dumps(templates_data, ensure_ascii=False, indent=2))
        elif output_format == "short":
            # 简短格式，仅ID和名称
            for t in templates:
                console.print(f"{t.id}: {t.name}")
        else:
            # 表格格式
            table = Table(title="模板列表")
            table.add_column("ID", style="cyan")
            table.add_column("名称", style="green")
            table.add_column("类型", style="blue")
            table.add_column("描述")

            for t in templates:
                table.add_row(t.id, t.name, t.type, t.description[:50] + "..." if len(t.description) > 50 else t.description)

            console.print(table)
            console.print(f"共 {len(templates)} 个模板")

    finally:
        session.close()


def handle_template_show(args: argparse.Namespace) -> None:
    """
    处理模板查看命令

    Args:
        args: 命令行参数
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 获取模板ID（可能是template_id或id）
        template_id = None
        if hasattr(args, "template_id"):
            template_id = args.template_id
        elif hasattr(args, "id"):
            template_id = args.id
        else:
            console.print("[bold red]错误: 未提供模板ID[/bold red]")
            return

        # 获取模板
        template = template_manager.get_template(template_id)
        if not template:
            console.print(f"[bold red]错误: 模板 {template_id} 不存在[/bold red]")
            return

        # 设置默认格式
        output_format = "text"
        if hasattr(args, "format"):
            output_format = args.format

        # 根据格式输出
        if output_format == "json":
            # JSON格式
            template_data = template.dict()
            console.print(json.dumps(template_data, ensure_ascii=False, indent=2))
        else:
            # 文本格式
            console.print(f"[bold cyan]ID:[/bold cyan] {template.id}")
            console.print(f"[bold green]名称:[/bold green] {template.name}")
            console.print(f"[bold blue]类型:[/bold blue] {template.type}")
            console.print(f"[bold]描述:[/bold] {template.description}")

            if hasattr(template, "metadata") and template.metadata:
                console.print("[bold]元数据:[/bold]")
                console.print(f"  作者: {template.metadata.author}")
                console.print(f"  版本: {template.metadata.version}")
                if template.metadata.tags:
                    console.print(f"  标签: {', '.join(template.metadata.tags)}")

            if hasattr(template, "variables") and template.variables:
                console.print("[bold]变量:[/bold]")
                for var in template.variables:
                    required_mark = "*" if getattr(var, "required", True) else ""
                    default_value = f" (默认值: {var.default})" if hasattr(var, "default") and var.default is not None else ""
                    console.print(f"  {var.name}{required_mark}: {var.type}{default_value}")
                    if hasattr(var, "description") and var.description:
                        console.print(f"    {var.description}")

            console.print("[bold]内容:[/bold]")
            console.print(template.content[:500] + "..." if len(template.content) > 500 else template.content)

    finally:
        session.close()


def handle_template_delete(args: argparse.Namespace) -> None:
    """
    处理模板删除命令

    Args:
        args: 命令行参数
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 获取模板ID（可能是template_id或id）
        template_id = None
        if hasattr(args, "template_id"):
            template_id = args.template_id
        elif hasattr(args, "id"):
            template_id = args.id
        else:
            console.print("[bold red]错误: 未提供模板ID[/bold red]")
            return

        # 检查模板是否存在
        template = template_manager.get_template(template_id)
        if not template:
            console.print(f"[bold red]错误: 模板 {template_id} 不存在[/bold red]")
            return

        # 删除模板
        success = template_manager.delete_template(template_id)
        if success:
            console.print(f"[bold green]成功删除模板: {template_id}[/bold green]")
        else:
            console.print(f"[bold red]删除模板失败: {template_id}[/bold red]")

    finally:
        session.close()


def handle_template_export(args: argparse.Namespace) -> None:
    """
    处理模板导出命令

    Args:
        args: 命令行参数
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 获取模板ID
        template_id = args.template_id

        # 获取模板
        template = template_manager.get_template(template_id)
        if not template:
            console.print(f"[bold red]错误: 模板 {template_id} 不存在[/bold red]")
            return

        # 设置输出格式
        format_type = "yaml"
        if hasattr(args, "format"):
            format_type = args.format

        # 获取输出路径
        output_path = None
        if hasattr(args, "output") and args.output:
            output_path = args.output

        # 导出模板
        result = template_manager.export_template(template_id, format_type, output_path)

        if output_path:
            console.print(f"[bold green]模板已导出到: {output_path}[/bold green]")
        else:
            console.print(result)

    finally:
        session.close()
