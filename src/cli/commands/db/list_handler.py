"""
数据库列表处理模块

列出数据库实体
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


class ListHandler(ClickBaseHandler):
    """数据库列表命令处理器"""

    VALID_TYPES = {"epic", "story", "task", "label", "template"}
    VALID_FORMATS = {"table", "json", "yaml"}

    def __init__(self):
        super().__init__()

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证列表命令参数

        Args:
            **kwargs: 命令参数

        Returns:
            bool: 验证是否通过

        Raises:
            ValidationError: 验证失败时抛出
        """
        entity_type = kwargs.get("type")
        output_format = kwargs.get("format", "table")

        if not entity_type:
            raise ValidationError("实体类型不能为空")

        if entity_type not in self.VALID_TYPES:
            raise ValidationError(f"不支持的实体类型: {entity_type}")

        if output_format not in self.VALID_FORMATS:
            raise ValidationError(f"不支持的输出格式: {output_format}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        """
        处理列表命令

        Args:
            **kwargs: 命令参数

        Returns:
            int: 0表示成功，1表示失败

        Raises:
            DatabaseError: 数据库操作失败时抛出
        """
        entity_type = kwargs.get("type")
        verbose = kwargs.get("verbose", False)
        output_format = kwargs.get("format", "table")
        service = kwargs.get("service")

        if verbose:
            console.print(f"列出所有 {entity_type}")

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            entities = service.get_entities(entity_type)
            return self._format_and_display_entities(entities, entity_type, output_format)
        except Exception as e:
            raise DatabaseError(f"列出 {entity_type} 失败: {str(e)}")

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
            display_method = getattr(self, f"_display_{entity_type}_table", self._display_generic_table)
            display_method(entities, entity_type)

        return 0

    def _display_task_table(self, tasks: List[Dict], _: str) -> None:
        """显示任务表格"""
        table = Table(title="任务列表")
        table.add_column("ID", style="cyan")
        table.add_column("标题")
        table.add_column("状态", style="green")
        table.add_column("优先级")

        for task in tasks:
            table.add_row(
                str(task.get("id", "")),
                str(task.get("title", "")),
                str(task.get("status", "")),
                str(task.get("priority", "")),
            )

        console.print(table)

    def _display_epic_table(self, epics: List[Dict], _: str) -> None:
        """显示史诗表格"""
        table = Table(title="史诗列表")
        table.add_column("ID", style="cyan")
        table.add_column("标题")
        table.add_column("状态", style="green")
        table.add_column("任务数")

        for epic in epics:
            table.add_row(
                str(epic.get("id", "")),
                str(epic.get("title", "")),
                str(epic.get("status", "")),
                str(len(epic.get("tasks", []))),
            )

        console.print(table)

    def _display_story_table(self, stories: List[Dict], _: str) -> None:
        """显示故事表格"""
        table = Table(title="故事列表")
        table.add_column("ID", style="cyan")
        table.add_column("标题")
        table.add_column("状态", style="green")
        table.add_column("史诗")

        for story in stories:
            table.add_row(
                str(story.get("id", "")),
                str(story.get("title", "")),
                str(story.get("status", "")),
                str(story.get("epic_id", "")),
            )

        console.print(table)

    def _display_generic_table(self, entities: List[Dict], entity_type: str) -> None:
        """显示通用表格"""
        table = Table(title=f"{entity_type} 列表")

        # 获取所有字段
        all_fields = set()
        for entity in entities:
            all_fields.update(entity.keys())

        # 添加表头
        for field in sorted(list(all_fields)):
            table.add_column(field, style="cyan" if field == "id" else None)

        # 添加数据行
        for entity in entities:
            row = [str(entity.get(field, "")) for field in sorted(list(all_fields))]
            table.add_row(*row)

        console.print(table)

    def error_handler(self, error: Exception) -> None:
        """
        处理列表命令错误

        Args:
            error: 捕获的异常
        """
        if isinstance(error, (ValidationError, DatabaseError)):
            console.print(f"[red]{str(error)}[/red]")
        else:
            super().error_handler(error)


@click.command(name="list", help="列出数据库内容")
@click.option("--type", required=True, help="实体类型(epic/story/task/label/template)")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["table", "json", "yaml"]), default="table", help="输出格式")
@pass_service(service_type="db")
def list_db(service, type: str, verbose: bool, format: str) -> None:
    """
    列出数据库内容命令

    Args:
        service: 数据库服务实例
        type: 实体类型
        verbose: 是否显示详细信息
        format: 输出格式
    """
    handler = ListHandler()
    try:
        result = handler.execute(service=service, type=type, verbose=verbose, format=format)
        return result
    except Exception:
        return 1
