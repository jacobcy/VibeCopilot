"""
数据库删除处理模块

处理数据库删除相关命令
"""

import logging
from typing import Any, Dict, Optional

import click
from rich.console import Console

from src.cli.decorators import pass_service

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError
from .validators import validate_db_name

logger = logging.getLogger(__name__)
console = Console()


class DeleteHandler(ClickBaseHandler):
    """删除实体处理器"""

    VALID_TYPES = {"epic", "story", "task", "label", "template"}

    def __init__(self):
        super().__init__()

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证删除命令参数

        Args:
            **kwargs: 命令参数

        Returns:
            bool: 验证是否通过

        Raises:
            ValidationError: 验证失败时抛出
        """
        entity_type = kwargs.get("entity_type")
        entity_id = kwargs.get("entity_id")
        force = kwargs.get("force", False)

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if not entity_id:
            raise ValidationError("实体ID不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        if not force:
            raise ValidationError("删除操作需要使用 --force 参数确认")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """
        处理删除命令

        Args:
            **kwargs: 命令参数

        Returns:
            int: 0表示成功，1表示失败

        Raises:
            DatabaseError: 数据库操作失败时抛出
        """
        entity_type = kwargs.get("entity_type")
        entity_id = kwargs.get("entity_id")
        verbose = kwargs.get("verbose", False)
        service = kwargs.get("service")

        if verbose:
            console.print(f"删除 {entity_type} (ID: {entity_id})")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            # 检查实体是否存在
            entity = service.get_entity(entity_type, entity_id)
            if not entity:
                console.print(f"[yellow]未找到 {entity_type} 类型，ID为 {entity_id} 的条目[/yellow]")
                return 1

            # 删除实体
            success = service.delete_entity(entity_type, entity_id)
            if not success:
                raise DatabaseError(f"删除 {entity_type} (ID: {entity_id}) 失败")

            # 输出结果
            console.print(f"[green]成功删除 {entity_type} (ID: {entity_id})[/green]")
            return 0

        except Exception as e:
            raise DatabaseError(f"删除 {entity_type} (ID: {entity_id}) 失败: {str(e)}")

    def error_handler(self, error: Exception) -> None:
        """
        处理删除命令错误

        Args:
            error: 捕获的异常
        """
        if isinstance(error, (ValidationError, DatabaseError)):
            console.print(f"[red]{str(error)}[/red]")
        else:
            super().error_handler(error)


@click.group(name="delete", help="删除数据库条目")
def delete():
    """删除数据库条目命令组"""
    pass


@delete.command(name="entity", help="删除实体")
@click.argument("entity_type")
@click.argument("entity_id")
@click.option("--force", "-f", is_flag=True, help="强制删除，不提示确认")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def delete_entity(service, entity_type: str, entity_id: str, force: bool, verbose: bool):
    """
    删除实体命令

    Args:
        service: 数据库服务实例
        entity_type: 实体类型
        entity_id: 实体ID
        force: 是否强制删除
        verbose: 是否显示详细信息
    """
    handler = DeleteHandler()
    try:
        result = handler.execute(service=service, entity_type=entity_type, entity_id=entity_id, force=force, verbose=verbose)
        return result
    except Exception:
        return 1
