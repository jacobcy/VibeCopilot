"""
数据库命令模块 (Click 版本)

处理数据库相关的命令，包括初始化、备份、恢复等操作。
"""

from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table

from src.db.service import DatabaseService
from src.models.db.init_db import init_db as _init_db

console = Console()


@click.group(help="数据库管理命令")
def db():
    """数据库管理命令组"""
    pass


@db.command(name="init", help="初始化数据库")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@click.option("--force", is_flag=True, help="强制重新初始化数据库")
def init_db(verbose: bool, force: bool) -> None:
    """初始化数据库"""
    try:
        service = DatabaseService()
        result = _init_db(force_recreate=force)

        if verbose:
            console.print(f"[bold]初始化结果:[/bold] {result}")
        else:
            console.print("数据库初始化完成")
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")


@db.command(name="list", help="列出数据库内容")
@click.option("--type", required=True, help="实体类型(epic/story/task/label/template)")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="输出格式")
def list_db(type: str, verbose: bool, format: str) -> None:
    """列出数据库内容"""
    try:
        service = DatabaseService()
        entities = service.get_entities(type)

        if not entities:
            console.print(f"没有找到 {type} 类型的实体")
            return

        if format == "json":
            console.print_json(data=entities)
            return

        # 表格输出
        table = Table(title=f"{type} 列表", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=12)
        table.add_column("名称", min_width=20)
        if verbose:
            table.add_column("描述", min_width=40)

        for entity in entities:
            if entity and isinstance(entity, dict):
                row = [entity.get("id", "N/A"), entity.get("name", "N/A")]
                if verbose:
                    row.append(entity.get("description", "N/A"))
                table.add_row(*row)

        console.print(table)
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")


@db.command(name="backup", help="备份数据库")
@click.option("--path", help="备份文件路径")
def backup_db(path: Optional[str] = None) -> None:
    """备份数据库"""
    try:
        service = DatabaseService()
        result = service.backup(path)
        console.print(f"数据库已备份到: {result}")
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")


@db.command(name="restore", help="恢复数据库")
@click.argument("path")
def restore_db(path: str) -> None:
    """从备份文件恢复数据库"""
    try:
        service = DatabaseService()
        service.restore(path)
        console.print("数据库恢复完成")
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")


@db.command(name="clean", help="清理数据库")
@click.option("--force", is_flag=True, help="强制清理")
def clean_db(force: bool = False) -> None:
    """清理数据库"""
    try:
        service = DatabaseService()
        if force:
            service.clean()
            console.print("数据库已清理")
        else:
            console.print("请使用 --force 选项确认清理操作")
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")


@db.command(name="stats", help="显示数据库统计信息")
def db_stats() -> None:
    """显示数据库统计信息"""
    try:
        service = DatabaseService()
        stats = service.get_stats()

        table = Table(title="数据库统计信息", show_header=True, header_style="bold magenta")
        table.add_column("类型", style="dim", width=12)
        table.add_column("数量", justify="right")

        for entity_type, count in stats.items():
            table.add_row(entity_type, str(count))

        console.print(table)
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
