"""
数据库表状态和结构信息查询处理器模块

提供查询数据库表状态信息、结构和统计数据的处理逻辑。
"""

import json
import logging
from typing import Any, Dict, Optional

import click
import yaml
from rich.console import Console
from rich.table import Table

from src.cli.core.decorators import pass_service
from src.db import get_session
from src.db.utils.entity_mapping import get_valid_entity_types, map_entity_to_table
from src.db.utils.schema import get_all_tables, get_db_stats, get_table_schema, get_table_stats

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)
console = Console()


class StatusHandler(ClickBaseHandler):
    """数据库表状态和结构信息查询命令处理器"""

    VALID_FORMATS = {"table", "json", "yaml"}

    def __init__(self):
        super().__init__()

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证查询命令参数

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

        return True

    def _display_db_stats(self, stats: Dict[str, int], output_format: str, show_detail: bool = False) -> int:
        """显示数据库所有表的统计信息

        Args:
            stats: 从 get_db_stats 获取的统计字典
            output_format: 输出格式
            show_detail: 是否显示详细信息

        Returns:
            int: 0表示成功，1表示失败
        """
        try:
            # 创建简化版本和详细版本的信息结构
            simplified_stats = {"database_stats": {"total_tables": len(stats), "total_records": sum(stats.values())}}

            detailed_stats = {"database_stats": {"tables": [], "total_tables": len(stats), "total_records": sum(stats.values())}}

            # 添加各表信息
            for table_name, count in stats.items():
                detailed_stats["database_stats"]["tables"].append({"name": table_name, "record_count": count})

            # 根据是否显示详情选择输出内容
            if output_format == "json":
                if show_detail:
                    print(json.dumps(detailed_stats, indent=2, ensure_ascii=False))
                else:
                    # 简洁模式下只显示表名和记录数
                    simple_list = {"tables": list(stats.keys()), "total_tables": len(stats), "total_records": sum(stats.values())}
                    print(json.dumps(simple_list, indent=2, ensure_ascii=False))
            elif output_format == "yaml":
                if show_detail:
                    print(yaml.dump(detailed_stats, allow_unicode=True, sort_keys=False, default_flow_style=False))
                else:
                    # 简洁模式下只显示表名列表
                    simple_list = {"tables": list(stats.keys()), "total_tables": len(stats), "total_records": sum(stats.values())}
                    print(yaml.dump(simple_list, allow_unicode=True, sort_keys=False, default_flow_style=False))
            else:
                # 表格展示 - 在任何模式下都保持简洁
                table = Table(title="数据库统计信息", show_header=True, header_style="bold magenta")
                table.add_column("表名", style="cyan", width=15)

                if show_detail:
                    table.add_column("记录数", justify="right", width=10)

                    for table_name, count in stats.items():
                        table.add_row(table_name, str(count))
                else:
                    # 非detail模式下只显示表名
                    for table_name in stats.keys():
                        table.add_row(table_name)

                console.print(table)

                # 始终显示总表数和总记录数
                console.print(f"[bold]总表数: [cyan]{len(stats)}[/cyan][/bold]")
                console.print(f"[bold]总记录数: [cyan]{sum(stats.values())}[/cyan][/bold]")

            return 0
        except Exception as e:
            console.print(f"[red]格式化数据库统计信息失败: {str(e)}[/red]")
            # Log the error as well
            logger.error(f"格式化数据库统计信息失败: {e}", exc_info=True)
            return 1  # Indicate failure

    def _display_table_stats(self, schema_info: Dict[str, Any], table_stats: Dict[str, Any], output_format: str, show_examples: bool = False) -> int:
        """显示指定表的统计和结构信息

        Args:
            schema_info: 从 get_table_schema 获取的结构信息
            table_stats: 从 get_table_stats 获取的统计信息
            output_format: 输出格式
            show_examples: 是否显示示例数据

        Returns:
            int: 0表示成功，1表示失败
        """
        try:
            if "error" in schema_info:
                console.print(f"[red]{schema_info['error']}[/red]")
                return 1

            # 创建基础版本的表信息（包含列结构但不包含示例数据）
            basic_info = {
                "table_name": schema_info["table_name"],
                "record_count": schema_info["count"],
                "columns": [{"name": col["name"], "type": str(col["type"])} for col in schema_info["columns"]],
            }

            # 添加状态分布（如果有）
            if table_stats.get("status_distribution") and len(table_stats["status_distribution"]) > 0:
                basic_info["status_distribution"] = table_stats["status_distribution"]

            if output_format == "json":
                if show_examples:
                    # 输出完整信息
                    print(json.dumps(schema_info, indent=2, ensure_ascii=False))
                else:
                    # 输出基础信息（包含结构但无示例）
                    print(json.dumps(basic_info, indent=2, ensure_ascii=False))
            elif output_format == "yaml":
                table_name = schema_info.get("table_name", "unknown")  # Get table name for context
                if show_examples:
                    # 完整信息 - 根据需要优化示例数据
                    if table_name.lower() == "rules" and "examples" in schema_info:
                        # 为规则示例创建更加友好的结构
                        for i, example in enumerate(schema_info["examples"]):
                            if "content" in example and example["content"]:
                                # 截断内容以便更好地显示
                                content = example["content"]
                                if len(content) > 200:
                                    example["content"] = content[:200] + "..."

                    # 输出YAML格式（完整信息）
                    yaml_str = yaml.dump(schema_info, allow_unicode=True, sort_keys=False, default_flow_style=False)
                    print(yaml_str)
                else:
                    # 输出YAML格式（基础信息，包含列结构）
                    yaml_str = yaml.dump(basic_info, allow_unicode=True, sort_keys=False, default_flow_style=False)
                    print(yaml_str)
            else:  # table format
                # 表格展示基本信息
                console.print(f"[bold]表名: [cyan]{schema_info['table_name']}[/cyan][/bold]")
                console.print(f"[bold]记录数: [cyan]{schema_info['count']}[/cyan][/bold]")

                # 无论是否为detail模式，都显示列结构（但在非detail模式下简化显示）
                columns_table = Table(title="列结构", show_header=True)
                columns_table.add_column("列名", style="cyan")
                columns_table.add_column("类型")

                if show_examples:
                    # detail模式下显示完整列信息
                    columns_table.add_column("可空", justify="center")
                    columns_table.add_column("默认值")

                    for col in schema_info["columns"]:
                        columns_table.add_row(
                            col["name"], str(col["type"]), "是" if col["nullable"] else "否", str(col["default"]) if col["default"] is not None else ""
                        )
                else:
                    # 非detail模式下简化列信息
                    for col in schema_info["columns"]:
                        columns_table.add_row(col["name"], str(col["type"]))

                console.print(columns_table)

                # 显示状态分布（如果有）
                if table_stats.get("status_distribution") and len(table_stats["status_distribution"]) > 0:
                    status_table = Table(title="状态分布", show_header=True)
                    status_table.add_column("状态", style="cyan")
                    status_table.add_column("数量", justify="right")
                    status_table.add_column("占比", justify="right")

                    total = table_stats.get("total_count", schema_info.get("count", 0))
                    for status, count in table_stats["status_distribution"].items():
                        percentage = (count / total * 100) if total > 0 else 0
                        status_table.add_row(str(status), str(count), f"{percentage:.1f}%")

                    console.print(status_table)

                # 显示示例数据（如果请求）
                if show_examples and schema_info.get("examples"):
                    examples_table = Table(title="示例数据 (最多 3 条)", show_header=True)
                    col_names = [col["name"] for col in schema_info["columns"]]
                    for name in col_names:
                        examples_table.add_column(name)

                    for example_row in schema_info["examples"]:
                        row_data = [str(example_row.get(name, "")) for name in col_names]
                        examples_table.add_row(*row_data)

                    console.print(examples_table)
                elif show_examples:
                    console.print("[yellow]未找到示例数据.[/yellow]")

            return 0
        except Exception as e:
            # Log the error
            table_name_ctx = schema_info.get("table_name", "未知表") if "schema_info" in locals() else "未知表"
            logger.error(f"格式化表 {table_name_ctx} 信息失败: {e}", exc_info=True)
            console.print(f"[red]格式化表 {table_name_ctx} 信息失败: {str(e)}[/red]")
            return 1  # Indicate failure

    def error_handler(self, error: Exception) -> None:
        """
        处理错误

        Args:
            error: 捕获的异常
        """
        if isinstance(error, (ValidationError, DatabaseError)):
            console.print(f"[red]{str(error)}[/red]")
        else:
            console.print(f"[red]未知错误: {str(error)}[/red]")


@click.command(name="status", help="查询数据库表状态和结构信息")
@click.option("--type", default="all", help="表名称或实体类型，默认为所有表")
@click.option("--detail", is_flag=True, help="是否显示示例数据（仅适用于单表查询）")
@click.option("--format", type=click.Choice(["table", "json", "yaml"]), default="table", help="输出格式")
@pass_service(service_type="db")
def status_db(service, type: str = "all", detail: bool = False, format: str = "table") -> None:
    """查询数据库表状态和结构信息"""
    # Adjust format for rules table
    if type.lower() == "rules" and format == "table":
        format = "yaml"

    handler = StatusHandler()
    session = None
    exit_code = 0
    try:
        # --- Validation (doesn't need session) ---
        if format not in handler.VALID_FORMATS:
            raise ValidationError(f"不支持的输出格式: {format}")

        session = get_session()

        if type == "all":
            # --- Get All Stats ---
            db_stats_data = get_db_stats(session)
            handler._display_db_stats(db_stats_data, format, detail)
        else:
            # --- Get Single Table Stats & Schema ---
            entity_type_or_table_name = type  # User input

            # Attempt to map entity type to table name
            mapped_table_name = map_entity_to_table(entity_type_or_table_name)

            # Use mapped name if it's different and potentially valid, otherwise use original input
            table_name = mapped_table_name if mapped_table_name != entity_type_or_table_name else entity_type_or_table_name
            logger.info(f"Input type '{entity_type_or_table_name}' resolved to table name '{table_name}'")

            # Validate the final table name
            all_tables = get_all_tables(session)
            if table_name not in all_tables:
                # Provide better error message including valid entity types if input was likely an entity type
                valid_entities = get_valid_entity_types(session, include_tables=False)  # Get only entity names
                error_msg = f"未知的表名或实体类型: {entity_type_or_table_name}。"
                error_msg += f"\n可用表: {', '.join(sorted(all_tables))}"
                if entity_type_or_table_name in valid_entities:
                    # If the input was a valid entity type, suggest the correct table name
                    correct_table = map_entity_to_table(entity_type_or_table_name)
                    error_msg += f"\n提示: 您可能想查询表 '{correct_table}'。"
                elif entity_type_or_table_name not in valid_entities:
                    # Also list valid entity types if the input wasn't one
                    error_msg += f"\n可用实体类型: {', '.join(sorted(valid_entities))}"
                raise ValidationError(error_msg)

            schema_data = get_table_schema(session, table_name)  # Use potentially mapped table_name
            if "error" in schema_data:
                console.print(f"[red]获取表 '{table_name}' 结构失败: {schema_data['error']}[/red]")
                exit_code = 1
                raise click.Abort()

            table_stats_data = get_table_stats(session, table_name)  # Use potentially mapped table_name
            handler._display_table_stats(schema_data, table_stats_data, format, detail)

    except Exception as e:
        # Let friendly_error_handling decorator manage user output for Abort/other exceptions
        if not isinstance(e, (ValidationError, DatabaseError, click.Abort)):
            logger.error(f"执行 status 命令时出错: {e}", exc_info=True)
        if not isinstance(e, click.Abort):
            console.print(f"[red]执行 status 命令时发生错误: {str(e)}[/red]")
        exit_code = 1
        raise click.Abort()
    finally:
        if session:
            session.close()
        # Exit with the determined code if needed, though Abort handles non-zero exit
        # if exit_code != 0:
        #    ctx = click.get_current_context()
        #    ctx.exit(exit_code)
