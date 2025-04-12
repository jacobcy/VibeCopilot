"""
数据库备份处理模块

处理数据库备份相关命令
"""

import logging
import os
import shutil
from datetime import datetime
from typing import Any, Dict, Optional

import click
from rich.console import Console

from src.cli.decorators import pass_service
from src.models.db.init_db import get_db_path

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError
from .validators import validate_file_path

logger = logging.getLogger(__name__)
console = Console()


class BackupHandler(ClickBaseHandler):
    """数据库备份处理器"""

    def __init__(self):
        super().__init__()

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证备份命令参数

        Args:
            **kwargs: 命令参数

        Returns:
            bool: 验证是否通过

        Raises:
            ValidationError: 验证失败时抛出
        """
        output_path = kwargs.get("output")

        if output_path:
            # 检查输出目录是否存在
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                raise ValidationError(f"输出目录不存在: {output_dir}")

            # 检查输出路径是否可写
            if os.path.exists(output_path):
                if not os.access(output_path, os.W_OK):
                    raise ValidationError(f"输出文件无写入权限: {output_path}")
            else:
                if not os.access(output_dir, os.W_OK):
                    raise ValidationError(f"输出目录无写入权限: {output_dir}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """
        处理备份命令

        Args:
            **kwargs: 命令参数

        Returns:
            int: 0表示成功，1表示失败

        Raises:
            DatabaseError: 数据库操作失败时抛出
        """
        verbose = kwargs.get("verbose", False)
        output_path = kwargs.get("output")

        try:
            # 获取数据库文件路径
            db_path = get_db_path()

            # 检查数据库文件是否存在
            if not os.path.exists(db_path):
                raise DatabaseError(f"数据库文件不存在: {db_path}")

            # 如果没有指定输出路径，生成默认路径
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(os.path.dirname(db_path), "backups")
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                output_path = os.path.join(backup_dir, f"vibecopilot_db_{timestamp}.backup")

            if verbose:
                console.print(f"开始备份数据库到 {output_path}")

            # 复制数据库文件
            shutil.copy2(db_path, output_path)

            # 校验备份是否成功
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise DatabaseError("备份文件创建失败或为空")

            console.print(f"[green]数据库已成功备份到: {output_path}[/green]")
            return 0

        except Exception as e:
            raise DatabaseError(f"备份数据库失败: {str(e)}")

    def error_handler(self, error: Exception) -> None:
        """
        处理备份命令错误

        Args:
            error: 捕获的异常
        """
        if isinstance(error, (ValidationError, DatabaseError)):
            console.print(f"[red]{str(error)}[/red]")
        else:
            super().error_handler(error)


@click.command(name="backup", help="备份数据库")
@click.option("--output", "-o", help="备份文件输出路径")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def backup_db(service, output: Optional[str], verbose: bool):
    """
    备份数据库命令

    Args:
        service: 数据库服务实例
        output: 备份文件输出路径
        verbose: 是否显示详细信息
    """
    handler = BackupHandler()
    try:
        result = handler.execute(service=service, output=output, verbose=verbose)
        return result
    except Exception:
        return 1
