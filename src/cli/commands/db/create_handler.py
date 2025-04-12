"""
数据库创建处理模块

处理数据库创建相关命令
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.panel import Panel

from src.cli.decorators import pass_service

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError
from .validators import validate_db_name

logger = logging.getLogger(__name__)
console = Console()


class CreateHandler(ClickBaseHandler):
    """创建实体处理器"""

    VALID_TYPES = {"epic", "story", "task", "label", "template"}

    def __init__(self):
        super().__init__()

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证创建命令参数

        Args:
            **kwargs: 命令参数

        Returns:
            bool: 验证是否通过

        Raises:
            ValidationError: 验证失败时抛出
        """
        entity_type = kwargs.get("entity_type")
        data = kwargs.get("data")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        if not data:
            raise ValidationError("实体数据不能为空")

        try:
            if isinstance(data, str):
                data_dict = json.loads(data)
            else:
                data_dict = data

            if not isinstance(data_dict, dict):
                raise ValidationError("数据必须是JSON对象")

            if "title" not in data_dict and entity_type not in ["label"]:
                raise ValidationError("数据必须包含title字段")

        except json.JSONDecodeError as e:
            raise ValidationError(f"JSON解析失败: {str(e)}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """
        处理创建命令

        Args:
            **kwargs: 命令参数

        Returns:
            int: 0表示成功，1表示失败

        Raises:
            DatabaseError: 数据库操作失败时抛出
        """
        entity_type = kwargs.get("entity_type")
        data = kwargs.get("data")
        verbose = kwargs.get("verbose", False)
        service = kwargs.get("service")

        if verbose:
            console.print(f"创建 {entity_type} 实体")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            # 解析JSON数据
            if isinstance(data, str):
                data_dict = json.loads(data)
            else:
                data_dict = data

            logger.info(f"解析后的JSON数据: {data_dict}")

            # 验证并丰富数据
            enriched_data = self._validate_and_enrich_data(entity_type, data_dict)
            logger.info(f"最终数据: {enriched_data}")

            # 创建实体
            entity = service.create_entity(entity_type, enriched_data)
            logger.info(f"创建实体成功: {entity}")

            # 输出结果
            title = entity.get("title", entity.get("name", entity.get("id", "")))
            console.print(Panel(f"[green]成功创建 {entity_type}[/green]\nID: {entity['id']}\n标题: {title}"))
            return 0

        except Exception as e:
            raise DatabaseError(f"创建 {entity_type} 失败: {str(e)}")

    def _validate_and_enrich_data(self, entity_type: str, data: Dict) -> Dict:
        """
        验证并丰富实体数据

        Args:
            entity_type: 实体类型
            data: 实体数据

        Returns:
            Dict: 丰富后的数据

        Raises:
            ValidationError: 验证失败时抛出
        """
        # 生成ID（如果未提供）
        if "id" not in data:
            prefix = entity_type[0].upper()
            unique_id = str(uuid.uuid4())[:6]
            data["id"] = f"{prefix}{unique_id}"
            logger.info(f"自动生成ID: {data['id']}")

        # 添加时间戳
        current_time = datetime.now().isoformat()
        if "created_at" not in data:
            data["created_at"] = current_time
        if "updated_at" not in data:
            data["updated_at"] = data["created_at"]

        # 处理特定类型的数据
        if entity_type == "task":
            data = {
                "id": data["id"],
                "title": data["title"],
                "description": data.get("description", ""),
                "status": data.get("status", "todo"),
                "priority": data.get("priority", "P2"),
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
            }

        return data

    def error_handler(self, error: Exception) -> None:
        """
        处理创建命令错误

        Args:
            error: 捕获的异常
        """
        if isinstance(error, (ValidationError, DatabaseError)):
            console.print(f"[red]{str(error)}[/red]")
        else:
            super().error_handler(error)


@click.group(name="create", help="创建数据库条目")
def create():
    """创建数据库条目命令组"""
    pass


@create.command(name="entity", help="创建实体")
@click.argument("entity_type")
@click.argument("data")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def create_entity(service, entity_type: str, data: str, verbose: bool):
    """
    创建实体命令

    Args:
        service: 数据库服务实例
        entity_type: 实体类型
        data: JSON格式的实体数据
        verbose: 是否显示详细信息
    """
    handler = CreateHandler()
    try:
        result = handler.execute(service=service, entity_type=entity_type, data=data, verbose=verbose)
        return result
    except Exception:
        return 1
