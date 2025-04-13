"""
数据库查询处理模块

处理数据库查询相关命令
"""

import json
import logging
from typing import Any, Dict, List, Optional

import click
import yaml
from rich.console import Console
from rich.table import Table

from src.cli.decorators import pass_service

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError
from .validators import validate_db_name

logger = logging.getLogger(__name__)
console = Console()


class QueryBaseHandler(ClickBaseHandler):
    """查询命令基础处理器"""

    VALID_TYPES = {"epic", "story", "task", "label", "template"}
    VALID_FORMATS = {"text", "json", "yaml"}

    def __init__(self):
        super().__init__()

    def _format_and_display_entities(self, entities: List[Dict], entity_type: str, output_format: str) -> int:
        """格式化并显示实体列表"""
        if not entities:
            console.print(f"[yellow]未找到 {entity_type} 类型的条目[/yellow]")
            return 0

        if output_format == "json":
            print(json.dumps(entities, indent=2, ensure_ascii=False))
        elif output_format == "yaml":
            print(yaml.dump(entities, allow_unicode=True, sort_keys=False))
        else:
            table = Table(title=f"{entity_type} 列表")

            # 添加表头
            columns = entities[0].keys() if entities else []
            for column in columns:
                table.add_column(column, style="cyan")

            # 添加数据行
            for entity in entities:
                row = [str(entity.get(col, "")) for col in columns]
                table.add_row(*row)

            console.print(table)

        return 0

    def _format_and_display_entity(self, entity: Dict, entity_type: str, entity_id: str, output_format: str) -> int:
        """格式化并显示单个实体"""
        if not entity:
            console.print(f"[yellow]未找到 {entity_type} 类型，ID为 {entity_id} 的条目[/yellow]")
            return 1

        if output_format == "json":
            print(json.dumps(entity, indent=2, ensure_ascii=False))
        elif output_format == "yaml":
            print(yaml.dump(entity, allow_unicode=True, sort_keys=False))
        else:
            console.print(f"[bold]{entity_type} (ID: {entity_id})[/bold]")

            table = Table(show_header=False, box=None)
            table.add_column("字段", style="cyan")
            table.add_column("值")

            for key, value in entity.items():
                if key != "id":  # ID已在标题显示
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False)
                    table.add_row(key, str(value))

            console.print(table)

        return 0


class GetEntityHandler(QueryBaseHandler):
    """获取单个实体处理器"""

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """验证获取实体参数"""
        entity_type = kwargs.get("entity_type")
        entity_id = kwargs.get("entity_id")
        output_format = kwargs.get("format", "text")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if not entity_id:
            raise ValidationError("实体ID不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        if output_format not in self.VALID_FORMATS:
            raise ValidationError(f"不支持的输出格式: {output_format}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """处理获取实体命令"""
        entity_type = kwargs.get("entity_type")
        entity_id = kwargs.get("entity_id")
        output_format = kwargs.get("format", "text")
        verbose = kwargs.get("verbose", False)
        service = kwargs.get("service")

        if verbose:
            console.print(f"查询 {entity_type} (ID: {entity_id})")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            entity = service.get_entity(entity_type, entity_id)
            return self._format_and_display_entity(entity, entity_type, entity_id, output_format)
        except Exception as e:
            raise DatabaseError(f"查询 {entity_type} 失败: {str(e)}")


class SearchEntitiesHandler(QueryBaseHandler):
    """搜索实体处理器"""

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """验证搜索实体参数"""
        entity_type = kwargs.get("entity_type")
        query_string = kwargs.get("query_string")
        output_format = kwargs.get("format", "text")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if not query_string:
            raise ValidationError("搜索条件不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        if output_format not in self.VALID_FORMATS:
            raise ValidationError(f"不支持的输出格式: {output_format}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """处理搜索实体命令"""
        entity_type = kwargs.get("entity_type")
        query_string = kwargs.get("query_string")
        output_format = kwargs.get("format", "text")
        verbose = kwargs.get("verbose", False)
        service = kwargs.get("service")

        if verbose:
            console.print(f"搜索 {entity_type}，查询: {query_string}")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            entities = service.search_entities(entity_type, query_string)
            return self._format_and_display_entities(entities, entity_type, output_format)
        except Exception as e:
            raise DatabaseError(f"搜索 {entity_type} 失败: {str(e)}")


class ListEntitiesHandler(QueryBaseHandler):
    """列出所有实体处理器"""

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """验证列出实体参数"""
        entity_type = kwargs.get("entity_type")
        output_format = kwargs.get("format", "text")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        if output_format not in self.VALID_FORMATS:
            raise ValidationError(f"不支持的输出格式: {output_format}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """处理列出实体命令"""
        entity_type = kwargs.get("entity_type")
        output_format = kwargs.get("format", "text")
        verbose = kwargs.get("verbose", False)
        service = kwargs.get("service")

        if verbose:
            console.print(f"查询所有 {entity_type}")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            entities = service.get_entities(entity_type)
            return self._format_and_display_entities(entities, entity_type, output_format)
        except Exception as e:
            raise DatabaseError(f"查询 {entity_type} 失败: {str(e)}")


class QueryHandler(QueryBaseHandler):
    """通用查询处理器，用于处理db query命令"""

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """验证查询参数"""
        entity_type = kwargs.get("type")
        output_format = kwargs.get("format", "table")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """处理查询命令"""
        entity_type = kwargs.get("type")
        entity_id = kwargs.get("id")
        query_string = kwargs.get("query")
        output_format = kwargs.get("format", "table")
        verbose = kwargs.get("verbose", False)
        service = kwargs.get("service")

        if verbose:
            console.print(f"查询 {entity_type}")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            # 如果提供了ID，查询单个实体
            if entity_id:
                entity = service.get_entity(entity_type, entity_id)
                return self._format_and_display_entity(entity, entity_type, entity_id, output_format)
            # 如果提供了查询字符串，搜索实体
            elif query_string:
                entities = service.search_entities(entity_type, query_string)
                return self._format_and_display_entities(entities, entity_type, output_format)
            # 否则列出所有实体
            else:
                entities = service.get_entities(entity_type)
                return self._format_and_display_entities(entities, entity_type, output_format)
        except Exception as e:
            raise DatabaseError(f"查询 {entity_type} 失败: {str(e)}")


@click.group(name="query", help="数据库查询命令组")
def query():
    """数据库查询命令组"""
    pass


@query.command(name="get", help="查询单个实体")
@click.argument("entity_type")
@click.argument("entity_id")
@click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="输出格式")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def get_entity(service, entity_type: str, entity_id: str, format: str, verbose: bool):
    """
    查询单个实体

    Args:
        service: 数据库服务实例
        entity_type: 实体类型
        entity_id: 实体ID
        format: 输出格式
        verbose: 是否显示详细信息
    """
    handler = GetEntityHandler()
    try:
        result = handler.execute(service=service, entity_type=entity_type, entity_id=entity_id, format=format, verbose=verbose)
        return result
    except Exception:
        return 1


@query.command(name="search", help="搜索实体")
@click.argument("entity_type")
@click.argument("query_string")
@click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="输出格式")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def search_entities(service, entity_type: str, query_string: str, format: str, verbose: bool):
    """
    搜索实体

    Args:
        service: 数据库服务实例
        entity_type: 实体类型
        query_string: 搜索条件
        format: 输出格式
        verbose: 是否显示详细信息
    """
    handler = SearchEntitiesHandler()
    try:
        result = handler.execute(service=service, entity_type=entity_type, query_string=query_string, format=format, verbose=verbose)
        return result
    except Exception:
        return 1


@query.command(name="list", help="列出所有实体")
@click.argument("entity_type")
@click.option("--format", "-f", type=click.Choice(["text", "json", "yaml"]), default="text", help="输出格式")
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def list_entities(service, entity_type: str, format: str, verbose: bool):
    """
    列出所有实体

    Args:
        service: 数据库服务实例
        entity_type: 实体类型
        format: 输出格式
        verbose: 是否显示详细信息
    """
    handler = ListEntitiesHandler()
    try:
        result = handler.execute(service=service, entity_type=entity_type, format=format, verbose=verbose)
        return result
    except Exception:
        return 1
