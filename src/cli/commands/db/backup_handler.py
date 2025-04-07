"""
数据库备份处理器

处理数据库备份命令逻辑
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


class BackupHandler(BaseDatabaseCommand):
    """数据库备份处理器"""

    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self.console = Console()

    def handle(self, args: Dict) -> int:
        """处理备份命令

        Args:
            args: 命令参数

        Returns:
            执行结果代码
        """
        verbose = args.get("verbose", False)
        output_path = args.get("output")

        try:
            # 获取数据库文件路径
            db_path = get_db_path()

            # 检查数据库文件是否存在
            if not os.path.exists(db_path):
                self.console.print(f"[red]数据库文件不存在: {db_path}[/red]")
                return 1

            # 如果没有指定输出路径，生成默认路径
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(os.path.dirname(db_path), "backups")
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                output_path = os.path.join(backup_dir, f"vibecopilot_db_{timestamp}.backup")

            if verbose:
                self.console.print(f"开始备份数据库到 {output_path}")

            # 复制数据库文件
            shutil.copy2(db_path, output_path)

            # 校验备份是否成功
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                self.console.print("[red]备份文件创建失败或为空[/red]")
                return 1

            self.console.print(f"[green]数据库已成功备份到: {output_path}[/green]")
            return 0

        except Exception as e:
            logger.error(f"备份数据库失败: {e}")
            self.console.print(f"[red]备份数据库失败: {e}[/red]")
            return 1
