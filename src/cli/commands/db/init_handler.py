"""
数据库初始化处理模块

处理数据库初始化命令
"""

import logging
import os
from typing import Any, Dict, Optional

import click
from rich.console import Console

from src.cli.decorators import pass_service
from src.db import init_database

from .base_handler import ClickBaseHandler
from .exceptions import InitializationError

logger = logging.getLogger(__name__)
console = Console()


class InitHandler(ClickBaseHandler):
    """数据库初始化命令处理器"""

    def __init__(self):
        super().__init__()

    def pre_process(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理命令参数，确保force参数正确传递

        Args:
            **kwargs: 命令参数

        Returns:
            Dict[str, Any]: 处理后的参数
        """
        processed_args = super().pre_process(**kwargs)
        # 清理可能存在的环境变量
        if "FORCE_RECREATE" in os.environ:
            del os.environ["FORCE_RECREATE"]

        if "force" in processed_args:
            force = processed_args["force"]
            if isinstance(force, bool):
                os.environ["FORCE_RECREATE"] = str(force).lower()
        return processed_args

    def post_process(self, result: Any) -> Any:
        """
        后处理命令结果，清理环境变量

        Args:
            result: 处理结果

        Returns:
            Any: 后处理的结果
        """
        # 清理环境变量
        if "FORCE_RECREATE" in os.environ:
            del os.environ["FORCE_RECREATE"]
        return super().post_process(result)

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证初始化参数

        Args:
            **kwargs: 命令参数

        Returns:
            bool: 验证是否通过
        """
        # 初始化命令的参数较简单，主要验证force和verbose是否为布尔值
        force = kwargs.get("force", False)
        verbose = kwargs.get("verbose", False)

        if not isinstance(force, bool) or not isinstance(verbose, bool):
            return False

        return True

    def handle(self, service=None, **kwargs: Dict[str, Any]) -> bool:
        """
        处理初始化命令

        Args:
            service: 数据库服务实例
            **kwargs: 命令参数

        Returns:
            bool: 是否初始化成功

        Raises:
            InitializationError: 初始化失败时抛出
        """
        force = kwargs.get("force", False)
        verbose = kwargs.get("verbose", False)

        if verbose:
            console.print(f"初始化数据库，强制重建: {'是' if force else '否'}")

        try:
            success = init_database(force_recreate=force)

            if success:
                console.print("[green]数据库初始化成功[/green]")

                # 确保数据库服务也初始化成功
                if service:
                    console.print("[green]数据库服务初始化成功[/green]")
                    return True
                else:
                    console.print("[yellow]警告: 数据库表初始化成功，但服务初始化失败[/yellow]")
                    raise InitializationError("数据库服务初始化失败")
            else:
                raise InitializationError("数据库初始化失败")

        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            raise InitializationError(f"初始化数据库失败: {str(e)}")

    def error_handler(self, error: Exception) -> None:
        """
        处理初始化过程中的错误

        Args:
            error: 捕获的异常
        """
        if isinstance(error, InitializationError):
            console.print(f"[red]{str(error)}[/red]")
        else:
            super().error_handler(error)


@click.command(name="init", help="初始化数据库")
@click.option("--force", is_flag=True, help="强制重建数据库")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def init_db(service, force: bool = False, verbose: bool = False) -> None:
    """
    初始化数据库命令

    Args:
        service: 数据库服务实例
        force: 是否强制重建数据库
        verbose: 是否显示详细信息
    """
    handler = InitHandler()
    try:
        if verbose:
            click.echo(f"初始化数据库，强制重建: {'是' if force else '否'}")
        result = handler.execute(service=service, force=force, verbose=verbose)
        return 0 if result else 1
    except Exception:
        return 1
