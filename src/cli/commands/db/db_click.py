"""
数据库命令模块

包含所有数据库相关的命令
"""

import logging
from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table

from src.cli.commands.db.handlers.init_handler import init_db
from src.cli.commands.db.handlers.list_handler import list_db
from src.cli.commands.db.handlers.show_handler import show_db
from src.cli.decorators import pass_service

console = Console()
logger = logging.getLogger(__name__)


@click.group(name="db", help="数据库操作命令")
def db():
    """数据库操作命令组"""
    pass


@db.command(name="init", help="初始化数据库")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@click.option("--force", is_flag=True, help="强制重新初始化数据库")
@pass_service(service_type="db")
def init_db(service, verbose: bool, force: bool) -> int:
    """初始化数据库"""
    try:
        # 创建参数字典，与InitHandler兼容
        args_dict = {"verbose": verbose, "force": force, "service": service}

        # 实例化并执行InitHandler
        from src.cli.commands.db.handlers.init_handler import InitHandler

        init_handler = InitHandler()
        return init_handler.handle(**args_dict)
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@db.command(name="list", help="列出数据库内容")
@click.option("--type", required=True, help="实体类型(epic/story/task/label/template)")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["table", "json", "yaml"]), default="table", help="输出格式")
@pass_service(service_type="db")
def list_db(service, type: str, verbose: bool, format: str) -> int:
    """列出数据库内容"""
    try:
        if service is None:
            console.print("[red]错误: 数据库服务未成功创建[/red]")
            return 1

        logger.debug(f"Click命令收到数据库服务 (ID: {id(service)})")

        # 临时使用旧的 handler，后续会重构
        from src.cli.commands.db.handlers.list_handler import ListHandler

        list_handler = ListHandler()
        # 创建参数字典
        args_dict = {"type": type, "verbose": verbose, "format": format, "service": service}
        # 使用 ** 解包字典为关键字参数
        return list_handler.handle(**args_dict)
    except Exception as e:
        logger.error(f"列出数据库内容失败: {e}", exc_info=True)
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@db.command(name="show", help="显示数据库条目")
@click.option("--type", required=True, help="实体类型(epic/story/task/label/template)")
@click.option("--id", required=True, help="实体ID")
@click.option("--format", type=click.Choice(["table", "json", "yaml"]), default="table", help="输出格式")
@pass_service(service_type="db")
def show_db(service, type: str, id: str, format: str) -> int:
    """显示数据库条目"""
    try:
        # 创建参数字典，与ShowHandler兼容
        args_dict = {"type": type, "id": id, "format": format, "service": service}

        # 实例化并执行ShowHandler
        from src.cli.commands.db.handlers.show_handler import ShowHandler

        show_handler = ShowHandler()
        return show_handler.handle(**args_dict)
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@db.command(name="query", help="查询数据库")
@click.option("--type", required=True, help="实体类型(epic/story/task/label/template)")
@click.option("--id", help="实体ID")
@click.option("--query", help="查询字符串")
@click.option("--format", type=click.Choice(["table", "json", "yaml"]), default="table", help="输出格式")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def query_db(service, type: str, id: Optional[str] = None, query: Optional[str] = None, format: str = "table", verbose: bool = False) -> int:
    """查询数据库"""
    try:
        # 创建参数字典，与QueryHandler兼容
        args_dict = {"type": type, "id": id, "query": query, "format": format, "verbose": verbose, "service": service}

        # 实例化并执行QueryHandler
        from src.cli.commands.db.handlers.query_handler import QueryHandler

        query_handler = QueryHandler()
        return query_handler.handle(**args_dict)
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@db.command(name="create", help="创建数据库条目")
@click.option("--type", required=True, help="实体类型(epic/story/task/label/template)")
@click.option("--data", required=True, help="JSON格式的数据")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def create_db(service, type: str, data: str, verbose: bool = False) -> int:
    """创建数据库条目"""
    try:
        # 创建参数字典，与CreateHandler兼容
        args_dict = {"type": type, "data": data, "verbose": verbose, "service": service}

        # 实例化并执行CreateHandler
        from src.cli.commands.db.handlers.create_handler import CreateHandler

        create_handler = CreateHandler()
        return create_handler.handle(**args_dict)
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@db.command(name="update", help="更新数据库条目")
@click.option("--type", required=True, help="实体类型(epic/story/task/label/template)")
@click.option("--id", required=True, help="实体ID")
@click.option("--data", required=True, help="JSON格式的数据")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def update_db(service, type: str, id: str, data: str, verbose: bool = False) -> int:
    """更新数据库条目"""
    try:
        # 创建参数字典，与UpdateHandler兼容
        args_dict = {"type": type, "id": id, "data": data, "verbose": verbose, "service": service}

        # 实例化并执行UpdateHandler
        from src.cli.commands.db.handlers.update_handler import UpdateHandler

        update_handler = UpdateHandler()
        return update_handler.handle(**args_dict)
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@db.command(name="delete", help="删除数据库条目")
@click.option("--type", required=True, help="实体类型(epic/story/task/label/template)")
@click.option("--id", required=True, help="实体ID")
@click.option("--force", is_flag=True, help="强制删除，不提示确认")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def delete_db(service, type: str, id: str, force: bool = False, verbose: bool = False) -> int:
    """删除数据库条目"""
    try:
        # 创建参数字典，与DeleteHandler兼容
        args_dict = {"type": type, "id": id, "force": force, "verbose": verbose, "service": service}

        # 实例化并执行DeleteHandler
        from src.cli.commands.db.handlers.delete_handler import DeleteHandler

        delete_handler = DeleteHandler()
        return delete_handler.handle(**args_dict)
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@db.command(name="backup", help="备份数据库")
@click.option("--output", help="备份文件路径")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def backup_db(service, output: Optional[str] = None, verbose: bool = False) -> int:
    """备份数据库"""
    try:
        # 创建参数字典，与BackupHandler兼容
        args_dict = {"output": output, "verbose": verbose, "service": service}

        # 实例化并执行BackupHandler
        from src.cli.commands.db.handlers.backup_handler import BackupHandler

        backup_handler = BackupHandler()
        return backup_handler.handle(**args_dict)
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@db.command(name="restore", help="恢复数据库")
@click.argument("backup_file")
@click.option("--force", is_flag=True, help="强制恢复，不提示确认")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def restore_db(service, backup_file: str, force: bool = False, verbose: bool = False) -> int:
    """从备份文件恢复数据库"""
    try:
        # 创建参数字典，与RestoreHandler兼容
        args_dict = {"backup_file": backup_file, "force": force, "verbose": verbose, "service": service}

        # 实例化并执行RestoreHandler
        from src.cli.commands.db.handlers.restore_handler import RestoreHandler

        restore_handler = RestoreHandler()
        return restore_handler.handle(**args_dict)
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        return 1


@db.command(name="clean", help="清理数据库")
@click.option("--force", is_flag=True, help="强制清理")
@pass_service
def clean_db(service, force: bool = False) -> None:
    """清理数据库"""
    try:
        if not force:
            console.print("[yellow]请使用 --force 选项确认清理操作[/yellow]")
            return

        service.clean()
        console.print("[green]数据库已清理[/green]")
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")


@db.command(name="stats", help="显示数据库统计信息")
@pass_service
def db_stats(service) -> None:
    """显示数据库统计信息"""
    try:
        stats = service.get_stats()

        table = Table(title="数据库统计信息", show_header=True, header_style="bold magenta")
        table.add_column("类型", style="dim", width=12)
        table.add_column("数量", justify="right")

        for entity_type, count in stats.items():
            table.add_row(entity_type, str(count))

        console.print(table)
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")


# 注册命令
db.add_command(init_db)
db.add_command(list_db)
db.add_command(show_db)
db.add_command(query_db)
db.add_command(create_db)
db.add_command(update_db)
db.add_command(delete_db)

if __name__ == "__main__":
    db()
