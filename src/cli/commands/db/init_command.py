"""数据库初始化命令

提供数据库表创建和初始数据填充功能
"""

import logging
from typing import Any, Dict, List, Optional

from src.cli.command import Command
from src.models.db.init_db import init_db

logger = logging.getLogger(__name__)


class InitCommand(Command):
    """数据库初始化命令"""

    def __init__(self):
        """初始化命令"""
        super().__init__(name="init", description="初始化数据库", help_text="创建数据库表结构并填充初始数据")

    def execute(self, args: Dict[str, Any]) -> int:
        """执行命令

        Args:
            args: 命令参数

        Returns:
            int: 退出码，0表示成功
        """
        logger.info("开始初始化数据库...")

        try:
            success = init_db(force_recreate=args.force)

            if success:
                self.console.print("[green]数据库初始化成功[/green]")
                return 0
            else:
                self.console.print("[red]数据库初始化失败，请检查日志[/red]")
                return 1

        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            self.console.print(f"[red]数据库初始化失败: {e}[/red]")
            return 1

    def setup_parser(self, parser):
        """设置命令参数

        Args:
            parser: 命令行参数解析器
        """
        # 目前不需要特定参数
        pass
