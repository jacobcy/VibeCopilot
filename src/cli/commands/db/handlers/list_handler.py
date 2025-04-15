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
from src.db.utils.entity_mapping import get_valid_entity_types, map_entity_to_table, map_table_to_entity
from src.db.utils.schema import get_all_tables

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError
from .validators import validate_db_name

logger = logging.getLogger(__name__)
console = Console()


class ListHandler(ClickBaseHandler):
    """数据库列表命令处理器"""

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
        service = kwargs.get("service")

        # 如果提供了实体类型，需要验证其有效性
        if entity_type:
            try:
                # 获取有效的实体类型
                valid_types = get_valid_entity_types(service.session)

                # 检查是否为有效的实体类型
                if entity_type not in valid_types:
                    # 尝试将表名映射为实体类型
                    mapped_entity = map_table_to_entity(entity_type)
                    if mapped_entity != entity_type and mapped_entity in valid_types:
                        # 更新为正确的实体类型
                        kwargs["type"] = mapped_entity
                        logger.info(f"将表名/输入 {entity_type} 映射为实体类型 {mapped_entity}")
                    else:
                        # 如果是service中注册的实体类型就通过验证
                        if hasattr(service, "repo_map") and entity_type in service.repo_map:
                            pass
                        else:
                            # 既不是已知实体类型也不是可映射的表名
                            raise ValidationError(f"不支持的实体类型: {entity_type}，可用类型: {', '.join(sorted(valid_types))}")
            except Exception as e:
                logger.error(f"验证实体类型时出错: {str(e)}")
                # 如果获取实体类型失败，使用service.repo_map作为备选
                if hasattr(service, "repo_map") and service.repo_map:
                    if entity_type not in service.repo_map:
                        raise ValidationError(f"不支持的实体类型: {entity_type}，可用类型: {', '.join(sorted(service.repo_map.keys()))}")
                else:
                    # 最后的兜底方案
                    fallback_types = ["epic", "story", "task", "label", "template"]
                    if entity_type not in fallback_types:
                        raise ValidationError(f"不支持的实体类型: {entity_type}，可用类型: {', '.join(sorted(fallback_types))}")

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

        if not service:
            raise DatabaseError("数据库服务未初始化")

        try:
            # 执行验证（可能会修改entity_type）
            self.validate(**kwargs)

            # 重新获取可能被验证方法修改的entity_type
            entity_type = kwargs.get("type")

            # 如果没有提供实体类型，则显示所有可用的实体类型
            if not entity_type:
                return self._display_available_types(service, output_format)

            if verbose:
                console.print(f"列出所有 {entity_type}")

            # 检查实体类型是否在service.repo_map中
            if hasattr(service, "repo_map") and service.repo_map:
                if entity_type not in service.repo_map:
                    # 获取与该实体类型对应的表名
                    table_name = map_entity_to_table(entity_type)
                    console.print(f"[yellow]警告: {entity_type} 不是可查询的实体类型[/yellow]")
                    console.print(f"[yellow]可用的实体类型: {', '.join(sorted(service.repo_map.keys()))}[/yellow]")
                    console.print(f"[yellow]提示: 使用 'vc db status --type {table_name}' 查看表结构和基本信息[/yellow]")
                    return 0

            # 获取并显示实体列表
            entities = service.get_entities(entity_type)
            return self._format_and_display_entities(entities, entity_type, output_format)
        except Exception as e:
            if entity_type:
                error_msg = f"列出 {entity_type} 失败: {str(e)}"
            else:
                error_msg = f"列出实体类型失败: {str(e)}"
            raise DatabaseError(error_msg)

    def _display_available_types(self, service, output_format: str) -> int:
        """
        显示所有可用的实体类型

        Args:
            service: 数据库服务
            output_format: 输出格式

        Returns:
            int: 0表示成功，1表示失败
        """
        try:
            # 获取所有可用的实体类型
            available_types = []

            try:
                # 优先使用新的实体映射函数获取，不包含表
                available_types = get_valid_entity_types(service.session, include_tables=False)

                # 如果service有repo_map属性，与其交集取有真实实现的实体类型
                if hasattr(service, "repo_map") and service.repo_map:
                    repo_entities = set(service.repo_map.keys())
                    # 只保留在repo_map中实际存在的实体类型
                    available_types = sorted(list(set(available_types).intersection(repo_entities)))
            except Exception as e:
                logger.warning(f"获取有效实体类型失败: {str(e)}")
                # 如果新方法失败，直接使用repo_map
                if hasattr(service, "repo_map") and service.repo_map:
                    available_types = list(service.repo_map.keys())
                else:
                    # 最后的兜底方案
                    available_types = ["epic", "story", "task", "label", "template"]

            # 根据输出格式显示可用的实体类型
            if output_format == "json":
                print(json.dumps({"entity_types": available_types}, indent=2, ensure_ascii=False))
            elif output_format == "yaml":
                print(yaml.dump({"entity_types": available_types}, allow_unicode=True, sort_keys=False))
            else:
                # 表格展示
                table = Table(title="可查询的实体类型", show_header=True)
                table.add_column("类型", style="cyan")

                for type_name in sorted(available_types):
                    table.add_row(type_name)

                console.print(table)
                console.print(f"使用 --type <实体类型> 参数查看具体实体列表")
                console.print(f"提示: 若要查看数据库表结构，请使用 'vc db status' 命令")

            return 0
        except Exception as e:
            console.print(f"[red]获取可用实体类型失败: {str(e)}[/red]")
            return 1

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
@click.option("--type", required=False, help="实体类型(epic/story/task/label/template)，不指定则列出所有可用类型")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@click.option("--format", type=click.Choice(["table", "json", "yaml"]), default="table", help="输出格式")
@pass_service(service_type="db")
def list_db_cli(service, type: Optional[str] = None, verbose: bool = False, format: str = "table") -> None:
    """
    列出数据库内容命令

    Args:
        service: 数据库服务实例
        type: 实体类型，不指定则列出所有可用类型
        verbose: 是否显示详细信息
        format: 输出格式
    """
    handler = ListHandler()
    try:
        result = handler.execute(service=service, type=type, verbose=verbose, format=format)
        return result
    except Exception:
        return 1
