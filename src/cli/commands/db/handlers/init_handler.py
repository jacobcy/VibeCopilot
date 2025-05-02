"""
数据库初始化命令处理模块
"""

import logging

import click

from src.db import init_database

logger = logging.getLogger(__name__)


def handle_db_init(force: bool, verbose: bool):
    """处理数据库初始化命令

    Args:
        force (bool): 是否强制重新创建数据库
        verbose (bool): 是否显示详细日志
    """
    click.echo(f"正在初始化数据库... (强制: {force})")
    try:
        success, stats = init_database(force_recreate=force)
        if success:
            click.echo(click.style("✅ 数据库初始化成功", fg="green"))
            click.echo("初始化统计:")
            for key, stat in stats.items():
                click.echo(f"  - {key.capitalize()}: 成功 {stat.get('success', 0)}, 失败 {stat.get('failed', 0)}")
        else:
            click.echo(click.style("❌ 初始化数据库失败", fg="red"))
            click.echo("错误: 初始化数据库失败")
            # 错误已经在init_database中记录
            if verbose:
                click.echo("请检查日志获取详细错误信息")
    except Exception as e:
        error_msg = f"数据库初始化过程中发生意外错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        click.echo(click.style(f"❌ {error_msg}", fg="red"))
        if verbose:
            click.echo(f"详细错误: {e}")
