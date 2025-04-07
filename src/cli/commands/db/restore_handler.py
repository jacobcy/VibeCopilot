"""
数据库恢复处理器

处理数据库恢复命令逻辑
"""

import logging
import os
import shutil
from datetime import datetime
from typing import Dict

from rich.console import Console

from src.cli.commands.db.base import BaseDatabaseCommand
from src.models.db.init_db import get_db_path

logger = logging.getLogger(__name__)


class RestoreHandler(BaseDatabaseCommand):
    """数据库恢复处理器"""

    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self.console = Console()

    def handle(self, args: Dict) -> int:
        """处理恢复命令

        Args:
            args: 命令参数

        Returns:
            执行结果代码
        """
        verbose = args.get("verbose", False)
        backup_file = args.get("backup_file")
        force = args.get("force", False)

        if not os.path.exists(backup_file):
            self.console.print(f"[red]备份文件不存在: {backup_file}[/red]")
            return 1

        # 校验备份文件有效性
        if os.path.getsize(backup_file) == 0:
            self.console.print(f"[red]备份文件为空: {backup_file}[/red]")
            return 1

        try:
            # 获取数据库文件路径
            db_path = get_db_path()

            # 如果数据库文件已存在且未指定强制恢复，询问用户
            if os.path.exists(db_path) and not force:
                self.console.print("[yellow]警告: 现有数据库将被覆盖，请添加 --force 参数确认此操作[/yellow]")
                return 1

            if verbose:
                self.console.print(f"从 {backup_file} 恢复数据库")

            # 创建备份（以防恢复失败）
            if os.path.exists(db_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_before_restore = f"{db_path}.before_restore.{timestamp}"
                shutil.copy2(db_path, backup_before_restore)
                if verbose:
                    self.console.print(f"已创建恢复前备份: {backup_before_restore}")

            # 复制备份文件到数据库位置
            shutil.copy2(backup_file, db_path)

            # 校验恢复结果
            if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
                self.console.print("[red]数据库恢复失败，目标文件不存在或为空[/red]")
                return 1

            self.console.print(f"[green]数据库已从 {backup_file} 成功恢复[/green]")
            return 0

        except Exception as e:
            logger.error(f"恢复数据库失败: {e}")
            self.console.print(f"[red]恢复数据库失败: {e}[/red]")
            return 1
