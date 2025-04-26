"""
数据库更新处理模块

处理数据库更新相关命令
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.table import Table

from src.cli.core.decorators import pass_service

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError
from .validators import validate_db_name

logger = logging.getLogger(__name__)
console = Console()


class UpdateHandler(ClickBaseHandler):
    """更新实体处理器"""

    VALID_TYPES = {"epic", "story", "task", "label", "template"}

    def __init__(self):
        super().__init__()

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证更新命令参数

        Args:
            **kwargs: 命令参数

        Returns:
            bool: 验证是否通过

        Raises:
            ValidationError: 验证失败时抛出
        """
        entity_type = kwargs.get("entity_type")
        entity_id = kwargs.get("entity_id")
        data = kwargs.get("data")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if not entity_id:
            raise ValidationError("实体ID不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        if not data:
            raise ValidationError("更新数据不能为空")

        try:
            if isinstance(data, str):
                data_dict = json.loads(data)
            else:
                data_dict = data

            if not isinstance(data_dict, dict):
                raise ValidationError("数据必须是JSON对象")

        except json.JSONDecodeError as e:
            raise ValidationError(f"JSON解析失败: {str(e)}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """
        处理更新命令

        Args:
            **kwargs: 命令参数

        Returns:
            int: 0表示成功，1表示失败

        Raises:
            DatabaseError: 数据库操作失败时抛出
        """
        entity_type = kwargs.get("entity_type")
        entity_id = kwargs.get("entity_id")
        data = kwargs.get("data")
        verbose = kwargs.get("verbose", False)
        service = kwargs.get("service")

        if verbose:
            console.print(f"更新 {entity_type} (ID: {entity_id})")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            # 检查实体是否存在
            entity = service.get_entity(entity_type, entity_id)
            if not entity:
                console.print(f"[yellow]未找到 {entity_type} 类型，ID为 {entity_id} 的条目[/yellow]")
                return 1

            # 解析JSON数据
            if isinstance(data, str):
                update_data = json.loads(data)
            else:
                update_data = data

            logger.info(f"解析后的JSON数据: {update_data}")

            # 验证并准备更新数据
            prepared_data = self._validate_and_prepare_update_data(entity_type, entity_id, update_data, entity)
            logger.info(f"准备更新的数据: {prepared_data}")

            # 更新实体
            updated_entity = service.update_entity(entity_type, entity_id, prepared_data)
            if not updated_entity:
                raise DatabaseError(f"更新 {entity_type} (ID: {entity_id}) 失败")

            # 输出结果
            console.print(f"[green]成功更新 {entity_type} (ID: {entity_id})[/green]")
            self._display_updated_fields(updated_entity, prepared_data)
            return 0

        except Exception as e:
            raise DatabaseError(f"更新 {entity_type} (ID: {entity_id}) 失败: {str(e)}")

    def _validate_and_prepare_update_data(self, entity_type: str, entity_id: str, data: Dict, original_entity: Dict) -> Dict:
        """
        验证并准备更新数据

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            data: 更新数据
            original_entity: 原始实体数据

        Returns:
            Dict: 准备好的更新数据

        Raises:
            ValidationError: 验证失败时抛出
        """
        # 禁止修改ID
        if "id" in data and data["id"] != entity_id:
            raise ValidationError("不允许修改实体ID")

        # 更新时间戳
        data["updated_at"] = datetime.now().isoformat()

        return data

    def _display_updated_fields(self, updated_entity: Dict, updated_fields: Dict) -> None:
        """
        显示更新后的字段

        Args:
            updated_entity: 更新后的实体
            updated_fields: 更新的字段
        """
        table = Table(show_header=False, box=None)
        table.add_column("字段", style="cyan")
        table.add_column("值")

        for key, value in updated_entity.items():
            if key in updated_fields:  # 只显示被更新的字段
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                table.add_row(key, str(value))

        console.print(table)

    def error_handler(self, error: Exception) -> None:
        """
        处理更新命令错误

        Args:
            error: 捕获的异常
        """
        if isinstance(error, (ValidationError, DatabaseError)):
            console.print(f"[red]{str(error)}[/red]")
        else:
            super().error_handler(error)


@click.group(name="update", help="更新数据库条目")
def update():
    """更新数据库条目命令组"""
    pass


@update.command(name="entity", help="更新实体")
@click.argument("entity_type")
@click.argument("entity_id")
@click.argument("data")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def update_entity(service, entity_type: str, entity_id: str, data: str, verbose: bool):
    """
    更新实体命令

    Args:
        service: 数据库服务实例
        entity_type: 实体类型
        entity_id: 实体ID
        data: JSON格式的更新数据
        verbose: 是否显示详细信息
    """
    handler = UpdateHandler()
    try:
        result = handler.execute(service=service, entity_type=entity_type, entity_id=entity_id, data=data, verbose=verbose)
        return result
    except Exception:
        return 1
