#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Click版本的template命令实现
提供模板的增删改查和生成功能
"""

import json
import logging
from typing import Dict, List, Optional, Union

import click
from rich.console import Console
from rich.table import Table

from src.db import get_session_factory
from src.templates.core.template_manager import TemplateManager

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
console = Console()


class TemplateContext:
    def __init__(self):
        session_factory = get_session_factory()
        self.session = session_factory()
        self.manager = TemplateManager(self.session)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()


def process_result(result: Dict[str, Union[bool, str, List, Dict]], show_table: bool = False):
    """处理并显示命令执行结果"""
    if not result.get("success", False):
        console.print(f"[bold red]错误:[/bold red] {result.get('error', '未知错误')}")
        return

    if show_table and "data" in result and isinstance(result["data"], list):
        table = Table(show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("名称", style="green")
        table.add_column("类型", style="yellow")
        table.add_column("描述")

        for item in result["data"]:
            if isinstance(item, dict):
                table.add_row(
                    str(item.get("id", "")),
                    item.get("name", ""),
                    item.get("type", ""),
                    item.get("description", "")[:80] + "..." if item.get("description", "") else "",
                )
        console.print(table)
    else:
        if "message" in result:
            console.print(f"[green]{result['message']}[/green]")
        if "data" in result:
            data = result["data"]
            if isinstance(data, list):
                for item in data:
                    _print_item(item)
            else:
                _print_item(data)


def _print_item(item):
    """打印单个项目的详细信息"""
    if hasattr(item, "dict"):
        item = item.dict()

    if isinstance(item, dict):
        if "id" in item and "name" in item:
            console.print(f"[bold]ID:[/bold] {item['id']}")
            console.print(f"[bold]名称:[/bold] {item['name']}")
            if "type" in item:
                console.print(f"[bold]类型:[/bold] {item['type']}")
            if "description" in item:
                desc = item["description"]
                if len(desc) > 80:
                    desc = desc[:80] + "..."
                console.print(f"[bold]描述:[/bold] {desc}")
            console.print("-" * 40)
        elif "file_path" in item:
            console.print(f"[bold]文件路径:[/bold] {item['file_path']}")
            if "content_length" in item:
                console.print(f"[bold]内容长度:[/bold] {item['content_length']} 字符")
            console.print("-" * 40)
    else:
        console.print(str(item))


@click.group(help="模板管理命令，提供模板的增删改查和生成功能")
def template():
    """模板管理命令组"""
    pass


@template.command()
@click.option("--type", "template_type", type=click.Choice(["rule", "command", "doc", "flow", "roadmap", "general"]), help="模板类型筛选")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
def list(template_type: Optional[str] = None, verbose: bool = False):
    """列出所有模板"""
    with TemplateContext() as ctx:
        templates = ctx.manager.get_all_templates()
        result = {"success": True, "data": [template.dict() for template in templates] if templates else []}
        process_result(result, show_table=not verbose)


@template.command()
@click.argument("template_id")
@click.option("--format", "output_format", type=click.Choice(["json", "text"]), default="text", help="输出格式")
def show(template_id: str, output_format: str):
    """查看模板详情"""
    with TemplateContext() as ctx:
        template = ctx.manager.get_template(template_id)
        if not template:
            result = {"success": False, "error": f"模板 '{template_id}' 不存在"}
        else:
            result = {"success": True, "data": template.dict() if output_format == "json" else template}
        process_result(result)


@template.command()
@click.option("--name", required=True, help="模板名称")
@click.option("--type", "template_type", required=True, type=click.Choice(["rule", "command", "doc", "flow", "roadmap", "general"]), help="模板类型")
def create(name: str, template_type: str):
    """创建新模板"""
    with TemplateContext() as ctx:
        try:
            template = ctx.manager.create_template(name=name, template_type=template_type)
            result = {"success": True, "message": f"成功创建模板 '{name}'", "data": template.dict()}
        except Exception as e:
            result = {"success": False, "error": str(e)}
        process_result(result)


@template.command()
@click.argument("template_id")
@click.option("--name", help="新的模板名称")
def update(template_id: str, name: Optional[str]):
    """更新模板"""
    with TemplateContext() as ctx:
        try:
            template = ctx.manager.update_template(template_id, name=name)
            result = {"success": True, "message": f"成功更新模板 '{template_id}'", "data": template.dict()}
        except Exception as e:
            result = {"success": False, "error": str(e)}
        process_result(result)


@template.command()
@click.argument("template_id")
@click.option("--force", is_flag=True, help="强制删除，不提示确认")
def delete(template_id: str, force: bool):
    """删除模板"""
    if not force and not click.confirm(f"确定要删除模板 {template_id} 吗?"):
        return

    with TemplateContext() as ctx:
        try:
            ctx.manager.delete_template(template_id)
            result = {"success": True, "message": f"成功删除模板 '{template_id}'"}
        except Exception as e:
            result = {"success": False, "error": str(e)}
        process_result(result)


@template.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--overwrite", is_flag=True, help="覆盖已存在的模板")
@click.option("--recursive", is_flag=True, help="递归导入目录下的所有模板")
def import_template(file_path: str, overwrite: bool, recursive: bool):
    """导入模板"""
    with TemplateContext() as ctx:
        try:
            imported = ctx.manager.import_template(file_path, overwrite=overwrite, recursive=recursive)
            result = {"success": True, "message": f"成功导入 {len(imported)} 个模板", "data": [template.dict() for template in imported]}
        except Exception as e:
            result = {"success": False, "error": str(e)}
        process_result(result)


@template.command()
@click.argument("template_id")
@click.option("--output", help="输出文件路径")
@click.option("--format", "export_format", type=click.Choice(["json", "yaml", "text"]), default="json", help="导出格式")
def export(template_id: str, output: Optional[str], export_format: str):
    """导出模板"""
    with TemplateContext() as ctx:
        try:
            exported = ctx.manager.export_template(template_id, output_path=output, format=export_format)
            result = {"success": True, "message": f"成功导出模板 '{template_id}'", "data": {"file_path": output} if output else {"content": exported}}
        except Exception as e:
            result = {"success": False, "error": str(e)}
        process_result(result)


@template.command()
@click.argument("template_id")
@click.argument("output_file")
@click.option("--vars", help="变量JSON字符串")
def generate(template_id: str, output_file: str, vars: Optional[str]):
    """使用模板生成内容"""
    variables = {}
    if vars:
        try:
            variables = json.loads(vars)
        except json.JSONDecodeError:
            console.print("[red]错误: 变量JSON格式不正确[/red]")
            return

    with TemplateContext() as ctx:
        try:
            ctx.manager.generate_template(template_id, output_file, variables)
            result = {"success": True, "message": f"成功生成文件 '{output_file}'"}
        except Exception as e:
            result = {"success": False, "error": str(e)}
        process_result(result)


@template.command()
@click.option("--force", is_flag=True, help="强制初始化，覆盖现有数据")
@click.option("--source", help="指定源目录")
def init(force: bool, source: Optional[str]):
    """初始化模板库"""
    if not force and not click.confirm("初始化将清空现有模板库，确定要继续吗?"):
        return

    with TemplateContext() as ctx:
        try:
            ctx.manager.init_templates(force=force, source_dir=source)
            result = {"success": True, "message": "成功初始化模板库"}
        except Exception as e:
            result = {"success": False, "error": str(e)}
        process_result(result)


if __name__ == "__main__":
    template()
