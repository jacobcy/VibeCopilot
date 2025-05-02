"""
数据库恢复处理模块

处理数据库恢复相关命令
"""

import logging
import os
import shutil
from datetime import datetime
from typing import Any, Dict, Optional

import click
from rich.console import Console

from src.cli.core.decorators import pass_service
from src.db.connection_manager import get_db_path

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError
from .validators import validate_file_path

logger = logging.getLogger(__name__)
console = Console()


class RestoreHandler(ClickBaseHandler):
    """数据库恢复处理器"""

    def __init__(self):
        super().__init__()

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证恢复命令参数

        Args:
            **kwargs: 命令参数

        Returns:
            bool: 验证是否通过

        Raises:
            ValidationError: 验证失败时抛出
        """
        backup_path = kwargs.get("backup_path")

        if not backup_path:
            raise ValidationError("必须指定备份文件路径")

        # 检查备份文件是否存在且可读
        if not os.path.exists(backup_path):
            raise ValidationError(f"备份文件不存在: {backup_path}")

        if not os.path.isfile(backup_path):
            raise ValidationError(f"指定路径不是文件: {backup_path}")

        if not os.access(backup_path, os.R_OK):
            raise ValidationError(f"备份文件无读取权限: {backup_path}")

        # 检查备份文件大小
        if os.path.getsize(backup_path) == 0:
            raise ValidationError("备份文件为空")

        return True

    def _get_db_path(self) -> str:
        """获取数据库文件路径"""
        return get_db_path()

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """
        处理恢复命令

        Args:
            **kwargs: 命令参数

        Returns:
            int: 0表示成功，1表示失败

        Raises:
            DatabaseError: 数据库操作失败时抛出
        """
        backup_path = kwargs.get("backup_path")
        force = kwargs.get("force", False)
        verbose = kwargs.get("verbose", False)

        try:
            # 获取数据库文件路径
            db_path = self._get_db_path()

            # 检查当前数据库文件
            if os.path.exists(db_path) and not force:
                raise DatabaseError("数据库文件已存在。如果要覆盖现有数据库，请使用 --force 选项")

            if verbose:
                console.print(f"开始从 {backup_path} 恢复数据库")

            # 如果存在现有数据库，先创建备份
            if os.path.exists(db_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(os.path.dirname(db_path), "backups")
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                auto_backup = os.path.join(backup_dir, f"vibecopilot_db_before_restore_{timestamp}.backup")
                shutil.copy2(db_path, auto_backup)
                if verbose:
                    console.print(f"已创建现有数据库备份: {auto_backup}")

            # 复制备份文件到数据库位置
            shutil.copy2(backup_path, db_path)

            # 校验恢复是否成功
            if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
                raise DatabaseError("数据库恢复失败或恢复后文件为空")

            console.print(f"[green]数据库已成功从 {backup_path} 恢复[/green]")
            return 0

        except Exception as e:
            raise DatabaseError(f"恢复数据库失败: {str(e)}")

    def error_handler(self, error: Exception) -> None:
        """
        处理恢复命令错误

        Args:
            error: 捕获的异常
        """
        if isinstance(error, (ValidationError, DatabaseError)):
            console.print(f"[red]{str(error)}[/red]")
        else:
            super().error_handler(error)


@click.command(name="restore", help="从备份文件恢复数据库")
@click.argument("backup_path", type=click.Path(exists=True))
@click.option("--force", "-f", is_flag=True, help="强制覆盖现有数据库")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def restore_db(service, backup_path: str, force: bool, verbose: bool):
    """
    从备份文件恢复数据库命令

    Args:
        service: 数据库服务实例
        backup_path: 备份文件路径
        force: 是否强制覆盖现有数据库
        verbose: 是否显示详细信息
    """
    handler = RestoreHandler()
    try:
        params: Dict[str, Any] = {"backup_path": backup_path, "force": force, "verbose": verbose}
        result = handler.execute(service=service, **params)
        return result
    except Exception:
        return 1
