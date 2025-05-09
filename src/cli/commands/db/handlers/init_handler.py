#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化处理模块
"""

import logging

import click
from rich import print as rich_print

from src.db.init_db import init_database
from src.utils.console_utils import print_error, print_success

logger = logging.getLogger(__name__)


def init_db_cli(force: bool = False) -> bool:
    """
    初始化数据库命令处理函数

    Args:
        force: 是否强制初始化，覆盖现有数据

    Returns:
        bool: 初始化是否成功
    """
    try:
        # 修改这里，根据init_database实际接受的参数
        # 如果init_database不接受force参数，则不传入
        init_database()  # 移除force参数

        # 如果需要force功能，但函数不支持，可以在这里添加警告
        if force:
            rich_print("[yellow]警告: force参数未生效，init_database()不支持此参数[/yellow]")

        print_success("数据库初始化成功")
        return True
    except Exception as e:
        logger.exception(f"数据库初始化失败: {e}")
        # 使用print_error代替未定义的console
        print_error(f"数据库初始化失败: {e}")
        return False


# 旧的 handle_db_init 函数现在被 init_db_cli 替代，可以移除或注释掉
# def handle_db_init(force: bool, verbose: bool): ...
