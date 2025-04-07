"""
数据库初始化处理模块

处理数据库初始化相关命令
"""

import logging
import os
from typing import Dict

from rich.console import Console

from src.cli.commands.db.base import BaseDatabaseCommand
from src.models.db.init_db import get_db_path, init_db

logger = logging.getLogger(__name__)


class InitHandler(BaseDatabaseCommand):
    """数据库初始化处理器"""

    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self.console = Console()

    def handle(self, args: Dict) -> int:
        """处理初始化命令

        Args:
            args: 命令参数

        Returns:
            执行结果代码
        """
        verbose = args.get("verbose", False)
        force = args.get("force", False)

        try:
            if verbose:
                self.console.print("开始初始化数据库...")

            # 如果使用force参数，先删除现有数据库
            if force:
                db_path = get_db_path()
                if os.path.exists(db_path):
                    if verbose:
                        self.console.print(f"正在删除现有数据库: {db_path}")
                    os.remove(db_path)

            # 使用init_db函数初始化数据库
            success = init_db()

            if success:
                self.console.print("[green]数据库初始化成功[/green]")
                return 0
            else:
                self.console.print("[red]数据库初始化失败，请检查日志[/red]")
                return 1
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            self.console.print(f"[red]初始化数据库失败: {e}[/red]")
            return 1
