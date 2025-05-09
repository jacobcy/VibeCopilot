"""
数据库命令组模块

只负责注册从 handlers 导入的命令。
"""

import click

from src.cli.commands.db.handlers.backup_handler import backup_db_cli

# 从 handlers 导入具体的 Click 命令函数
from src.cli.commands.db.handlers.init_handler import init_db_cli as init_db_handler
from src.cli.commands.db.handlers.list_handler import list_db_cli
from src.cli.commands.db.handlers.query_handler import query_db_cli
from src.cli.commands.db.handlers.restore_handler import restore_db_cli
from src.cli.commands.db.handlers.show_handler import show_db_cli
from src.cli.commands.db.handlers.status_handler import status_db_cli
from src.db.init_data import load_all_initial_data  # 导入初始数据加载函数


# 数据库命令组
@click.group(name="db", help="数据库管理命令")
def db():
    """数据库管理命令组"""
    pass


# 在这里将普通函数包装为click命令
@click.command(name="init")
@click.option("--force", is_flag=True, help="强制重新初始化数据库")
@click.option("--sample-data", is_flag=True, help="加载示例数据")
def init_db_cli(force=False, sample_data=False):
    """初始化数据库并导入初始数据"""
    try:
        # 调用原始的初始化函数
        result = init_db_handler(force)  # 暂时只传一个参数

        # 导入初始数据 - 修复导入路径
        from src.db import get_session  # 从正确的模块导入

        session = get_session()
        try:
            click.echo("正在导入初始数据...")
            load_all_initial_data(session)
            click.echo("初始数据导入完成")
            session.commit()
        except Exception as e:
            session.rollback()
            click.echo(f"导入初始数据时出错: {str(e)}")
        finally:
            session.close()
    except Exception as e:
        click.echo(f"初始化数据导入功能失败: {str(e)}")

    return result


db.add_command(init_db_cli)
db.add_command(list_db_cli)
db.add_command(show_db_cli)
db.add_command(query_db_cli)
db.add_command(backup_db_cli)
db.add_command(restore_db_cli)
db.add_command(status_db_cli)
