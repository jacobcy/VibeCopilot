"""
数据库命令组模块

定义数据库相关的CLI命令。
"""

from typing import Any, Dict

import click

from src.cli.commands.db.handlers.backup_handler import BackupHandler

# 导入处理函数
from src.cli.commands.db.handlers.init_handler import handle_db_init
from src.cli.commands.db.handlers.list_handler import handle_db_list
from src.cli.commands.db.handlers.query_handler import QueryHandler
from src.cli.commands.db.handlers.restore_handler import RestoreHandler
from src.cli.commands.db.handlers.show_handler import ShowHandler
from src.cli.commands.db.handlers.status_handler import StatusHandler
from src.cli.core.decorators import pass_service


# 数据库命令组
@click.group(name="db", help="数据库管理命令")
def db():
    pass


# 初始化命令
@db.command(name="init", help="初始化数据库")
@click.option("--force", is_flag=True, default=False, help="强制重新创建数据库")
@click.option("--verbose", is_flag=True, default=False, help="显示详细信息")
def init_command(force: bool, verbose: bool):
    """初始化数据库的Click命令入口"""
    handle_db_init(force=force, verbose=verbose)


# 列出实体命令
@db.command(name="list", help="列出数据库中的实体")
@click.option("-t", "--type", "entity_type", default="roadmap", help="要列出的实体类型 (e.g., roadmap, epic, milestone, story, task)")
@click.option("-v", "--verbose", is_flag=True, default=False, help="显示详细信息")
def list_command(entity_type: str, verbose: bool):
    """列出数据库实体的Click命令入口"""
    handle_db_list(entity_type=entity_type, verbose=verbose)


# 显示实体命令
@db.command(name="show", help="显示数据库条目")
@click.option("-i", "--id", required=True, help="实体ID")
def show_command(id: str):
    """显示数据库条目的Click命令入口"""
    handler = ShowHandler()
    params: Dict[str, Any] = {"id": id, "format": "yaml"}  # 始终使用YAML格式
    handler.handle(**params)


# 查询数据命令
@db.command(name="query", help="查询数据")
@click.option("-t", "--type", "entity_type", required=True, help="实体类型 (e.g., roadmap, epic, milestone, story, task)")
@click.option("-q", "--query", default=None, help="查询字符串")
@click.option("-v", "--verbose", is_flag=True, default=False, help="显示详细信息")
@pass_service(service_type="db")
def query_command(service, entity_type: str, query: str, verbose: bool):
    """查询数据的Click命令入口"""
    handler = QueryHandler()
    params: Dict[str, Any] = {"type": entity_type, "query": query, "format": "yaml", "verbose": verbose, "service": service}  # 始终使用YAML格式  # 添加服务实例
    handler.handle(**params)


# 备份数据库命令
@db.command(name="backup", help="备份数据库")
@click.option("--output", default=None, help="输出文件路径")
@click.option("--verbose", is_flag=True, default=False, help="显示详细信息")
def backup_command(output: str, verbose: bool):
    """备份数据库的Click命令入口"""
    handler = BackupHandler()
    params: Dict[str, Any] = {"output": output, "verbose": verbose}
    handler.handle(**params)


# 恢复数据库命令
@db.command(name="restore", help="恢复数据库")
@click.argument("backup_file", required=True)
@click.option("--force", is_flag=True, default=False, help="强制恢复，不提示确认")
@click.option("--verbose", is_flag=True, default=False, help="显示详细信息")
def restore_command(backup_file: str, force: bool, verbose: bool):
    """恢复数据库的Click命令入口"""
    handler = RestoreHandler()
    params: Dict[str, Any] = {"backup_file": backup_file, "force": force, "verbose": verbose}
    handler.handle(**params)


# 数据库状态命令
@db.command(name="status", help="查询数据库表状态和结构信息")
@click.option("-t", "--type", default="all", help="表名称或实体类型，默认为所有表")
def status_command(type: str):
    """查询数据库表状态和结构信息的Click命令入口"""
    handler = StatusHandler()
    params: Dict[str, Any] = {"type": type, "detail": False, "format": "yaml"}  # 不显示示例数据  # 始终使用YAML格式
    handler.handle(**params)
