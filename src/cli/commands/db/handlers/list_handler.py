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

from src.cli.core.decorators import pass_service
from src.db import DatabaseService, get_session
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
        output_format = kwargs.get("format", "table")
        if output_format not in self.VALID_FORMATS:
            raise ValidationError(f"不支持的输出格式: {output_format}")
        # Simplified validation: type validation now happens in list_db_cli
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
        output_format = kwargs.get("format", "yaml")  # 默认使用YAML格式
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
                # 获取有效的实体类型
                valid_types = []
                if hasattr(service, "repo_map") and service.repo_map:
                    valid_types = list(service.repo_map.keys())
                return self._display_available_types(output_format, valid_types)

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
            entities = service.get_entities(service.session, entity_type=entity_type)
            return self._format_and_display_entities(entities, entity_type, output_format)
        except Exception as e:
            if entity_type:
                error_msg = f"列出 {entity_type} 失败: {str(e)}"
            else:
                error_msg = f"列出实体类型失败: {str(e)}"
            raise DatabaseError(error_msg)

    def _display_available_types(self, output_format: str, available_types: Optional[List[str]] = None) -> int:
        """显示所有可用的实体类型 (从传入列表)"""
        try:
            # Use the passed list or get valid types if None
            types_to_display = available_types or []

            if not types_to_display:
                console.print("[yellow]未找到可查询的实体类型。[/yellow]")
                return 0

            # 根据输出格式显示可用的实体类型
            if output_format == "json":
                print(json.dumps({"entity_types": sorted(types_to_display)}, indent=2, ensure_ascii=False))
            elif output_format == "yaml":
                print(yaml.dump({"entity_types": sorted(types_to_display)}, allow_unicode=True, sort_keys=False))
            else:
                # 表格展示
                table = Table(title="可查询的实体类型", show_header=True)
                table.add_column("类型", style="cyan")

                for type_name in sorted(types_to_display):
                    table.add_row(type_name)

                console.print(table)
                console.print(f"使用 --type <实体类型> 参数查看具体实体列表")
                console.print(f"提示: 若要查看数据库表结构，请使用 'vc db status' 命令")

            return 0
        except Exception as e:
            console.print(f"[red]格式化可用实体类型失败: {str(e)}[/red]")
            logger.error(f"格式化可用实体类型失败: {e}", exc_info=True)
            return 1

    def _simplify_roadmap_entities(self, entities: List[Dict]) -> List[Dict]:
        """简化 roadmap 实体，移除关联的 epics, stories 和 tasks"""
        simplified_entities = []
        for entity in entities:
            # 创建一个新的字典，只包含基本字段
            simplified_entity = {
                "id": entity.get("id", ""),
                "title": entity.get("title", ""),
                "description": entity.get("description", ""),
                "version": entity.get("version", ""),
                "status": entity.get("status", ""),
                "tags": entity.get("tags", []),
                "created_at": entity.get("created_at", ""),
                "updated_at": entity.get("updated_at", ""),
                "epics_count": len(entity.get("epics", [])),
                "milestones_count": len(entity.get("milestones", [])),
            }
            simplified_entities.append(simplified_entity)
        return simplified_entities

    def _format_and_display_entities(self, entities: List[Dict], entity_type: str, output_format: str) -> int:
        """格式化并显示实体列表"""
        if not entities:
            console.print(f"[yellow]未找到 {entity_type} 类型的条目[/yellow]")
            return 0

        # 对于 roadmap 类型，简化输出，不包含所有关联的 tasks
        if entity_type == "roadmap":
            entities = self._simplify_roadmap_entities(entities)

        if output_format == "json":
            # 对于 JSON 格式，直接输出简化后的实体列表
            print(json.dumps(entities, indent=2, ensure_ascii=False))
        else:
            # 默认使用 YAML 格式，直接输出简化后的实体列表
            print(yaml.dump(entities, allow_unicode=True, sort_keys=False))

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

    def _display_roadmap_table(self, roadmaps: List[Dict], _: str) -> None:
        """显示路线图表格"""
        table = Table(title="路线图列表")
        table.add_column("ID", style="cyan")
        table.add_column("标题")
        table.add_column("状态", style="green")
        table.add_column("版本")
        table.add_column("Epics数量")
        table.add_column("里程碑数量")
        table.add_column("创建时间")
        table.add_column("更新时间")

        for roadmap in roadmaps:
            table.add_row(
                str(roadmap.get("id", "")),
                str(roadmap.get("title", "")),
                str(roadmap.get("status", "")),
                str(roadmap.get("version", "")),
                str(roadmap.get("epics_count", 0)),
                str(roadmap.get("milestones_count", 0)),
                str(roadmap.get("created_at", "")),
                str(roadmap.get("updated_at", "")),
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
            # Let the friendly_error_handling decorator handle unexpected errors
            # console.print(f"[red]未知错误: {str(error)}[/red]")
            pass


@click.command(name="list", help="列出数据库内容")
@click.option("--type", required=False, help="要列出的实体类型 (如 epic, story, task 等)，不指定则列出所有可用类型")
@click.option("--verbose", is_flag=True, help="显示详细信息")
@pass_service(service_type="db")
def list_db_cli(service, type: Optional[str] = None, verbose: bool = False) -> None:
    """
    列出数据库内容命令

    Args:
        service: 数据库服务实例
        type: 实体类型，不指定则列出所有可用类型
        verbose: 是否显示详细信息
    """
    handler = ListHandler()
    session = None
    exit_code = 0
    try:
        # 始终使用YAML格式
        format = "yaml"

        session = get_session()

        if type:
            # --- Type specified: Validate, Get Entities, Display ---
            entity_type_input = type
            final_entity_type = entity_type_input  # Assume input is correct initially

            # --- Validation requiring session ---
            valid_types = get_valid_entity_types(session)  # Get all valid types from DB models

            if entity_type_input not in valid_types:
                # Try mapping table name to entity type
                temp_mapped = map_table_to_entity(entity_type_input)
                if temp_mapped != entity_type_input and temp_mapped in valid_types:
                    final_entity_type = temp_mapped
                    logger.info(f"将表名/输入 {entity_type_input} 映射为实体类型 {final_entity_type}")
                # Check if it's a type known directly by the service (even if not a primary mapped entity)
                elif hasattr(service, "repo_map") and entity_type_input in service.repo_map:
                    final_entity_type = entity_type_input
                else:
                    # Invalid type
                    console.print(f"[red]不支持的实体类型: {entity_type_input}，可用类型: {', '.join(sorted(valid_types))}[/red]")
                    exit_code = 1
                    raise click.Abort()  # Abort execution

            # --- Check if type exists in service repo_map before querying (optional but good practice) ---
            if hasattr(service, "repo_map") and service.repo_map:
                if final_entity_type not in service.repo_map:
                    # This type might be valid in the DB but not queryable via this service directly
                    table_name = map_entity_to_table(final_entity_type)
                    console.print(f"[yellow]警告: {final_entity_type} 不是此服务可直接查询的实体类型[/yellow]")
                    console.print(f"[yellow]服务支持的类型: {', '.join(sorted(service.repo_map.keys()))}[/yellow]")
                    entities = []  # Return empty list for display
                else:
                    # --- Get Entities (using session and correct entity type) ---
                    if verbose:
                        console.print(f"列出所有 {final_entity_type}")

                    # 对于 roadmap 类型，使用简化方法获取实体
                    if final_entity_type == "roadmap":
                        entities = service.get_entities_simplified(session, final_entity_type)
                    else:
                        # 对于其他类型，使用普通方法获取实体
                        entities = service.get_entities(session, final_entity_type)
            else:
                # Should not happen if service is initialized correctly
                logger.error("DatabaseService 未正确初始化 repo_map")
                console.print("[red]内部错误: 数据库服务配置不完整[/red]")
                exit_code = 1
                raise click.Abort()

            # --- Display Entities ---
            handler._format_and_display_entities(entities, final_entity_type, format)

        else:
            # --- No type specified: Display Available Types ---
            available_types = get_valid_entity_types(session, include_tables=False)
            # Intersect with service repo_map if available for more accuracy on what list command supports
            if hasattr(service, "repo_map") and service.repo_map:
                repo_entities = set(service.repo_map.keys())
                available_types = sorted(list(set(available_types).intersection(repo_entities)))

            handler._display_available_types(format, available_types=available_types)

    except Exception as e:
        # Let friendly_error_handling decorator manage user output for Abort/other exceptions
        if not isinstance(e, (ValidationError, DatabaseError, click.Abort)):
            logger.error(f"执行 list 命令时出错: {e}", exc_info=True)
        if not isinstance(e, click.Abort):
            console.print(f"[red]执行 list 命令时发生错误: {str(e)}[/red]")
        exit_code = 1
        # Re-raise Abort or allow decorator to handle it
        raise click.Abort()
    finally:
        if session:
            session.close()
        # Exit code is mainly handled by click.Abort now
        # if exit_code != 0:
        #    ctx = click.get_current_context()
        #    ctx.exit(exit_code)


def handle_db_list(entity_type: str, verbose: bool):
    """处理数据库列出实体的命令

    Args:
        entity_type (str): 要列出的实体类型
        verbose (bool): 是否显示详细日志
    """
    if verbose:
        click.echo(f"正在列出 '{entity_type}' 类型的实体...")

    try:
        # 创建数据库服务实例
        db_service = DatabaseService(verbose=verbose)

        with db_service.get_session() as session:
            # 对于 roadmap 类型，使用简化方法获取实体
            if entity_type == "roadmap":
                entities = db_service.get_entities_simplified(session, entity_type)
            else:
                entities = db_service.get_entities(session, entity_type)

        if not entities:
            click.echo(f"未找到类型为 '{entity_type}' 的实体。")
            return

        # 始终使用YAML格式输出
        print(yaml.dump(entities, allow_unicode=True, sort_keys=False))

    except ValueError as e:
        # 处理未知的实体类型错误
        click.echo(click.style(f"❌ 错误: {e}", fg="red"))
    except Exception as e:
        error_msg = f"列出实体时出错: {str(e)}"
        logger.error(error_msg, exc_info=True)
        click.echo(click.style(f"❌ {error_msg}", fg="red"))
        if verbose:
            click.echo(f"详细错误: {e}")
