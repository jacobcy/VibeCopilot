"""
数据库条目显示模块

显示数据库中的单个实体条目
"""

import json
import logging
from typing import Any, Dict, Optional

import click
import yaml
from rich.console import Console
from rich.table import Table
from sqlalchemy.orm.collections import InstrumentedList  # Import for checking relationships

from src.db.repositories.roadmap_repository import EpicRepository, MilestoneRepository, RoadmapRepository, StoryRepository
from src.db.repositories.task_repository import TaskRepository
from src.db.session_manager import session_scope
from src.utils.id_generator import EntityType, IdGenerator

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)
console = Console()


class ShowHandler(ClickBaseHandler):
    """数据库条目显示命令处理器"""

    def __init__(self):
        super().__init__()

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证显示命令参数

        Args:
            **kwargs: 命令参数 (只需要 id)

        Returns:
            bool: 验证是否通过

        Raises:
            ValidationError: 验证失败时抛出
        """
        entity_id = kwargs.get("id")

        if not entity_id:
            raise ValidationError("实体ID不能为空")

        try:
            entity_type_enum = IdGenerator.get_entity_type_from_id(entity_id)
            if entity_type_enum is None:
                # Check if it's a simple ID without prefix (e.g., for older data)
                # This part might need adjustment based on how non-prefixed IDs are handled
                if "_" not in entity_id:
                    logger.warning(f"ID '{entity_id}' lacks a standard prefix. Attempting to infer type.")
                    # Add logic here if you need to guess the type for non-prefixed IDs
                    # For now, we'll raise an error as standard IDs are expected
                    raise ValidationError(f"ID '{entity_id}' does not have a recognizable prefix.")
                else:
                    raise ValidationError(f"无法从ID '{entity_id}' 推断出有效的实体类型")

        except ValueError as e:  # Catches prefix errors from IdGenerator
            raise ValidationError(f"无效的实体ID格式: {entity_id}. {str(e)}")
        except ValidationError as e:  # Re-raise explicit validation errors
            raise e
        except Exception as e:  # Catch any other unexpected errors during ID parsing
            logger.error(f"Unexpected error validating ID '{entity_id}': {e}", exc_info=True)
            raise ValidationError(f"验证ID '{entity_id}' 时发生意外错误: {str(e)}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        entity_id = kwargs.get("id")
        # 获取 detail 标志，默认为 False (即默认非递归)
        show_detail = kwargs.get("detail", False)

        try:
            # 先验证ID格式和前缀
            self.validate(id=entity_id)

            # 成功验证后，再提取类型
            entity_type_enum = IdGenerator.get_entity_type_from_id(entity_id)  # Should not fail after validate
            entity_type_str = entity_type_enum.name.lower()

            logger.info(f"尝试显示类型 '{entity_type_str}' 的实体，ID: {entity_id}, ShowDetail: {show_detail}")

            # 定义 Repo 映射
            # 注意：这里可以考虑动态加载或使用服务发现模式，而不是硬编码
            repo_map = {
                "epic": EpicRepository(),
                "story": StoryRepository(),
                "task": TaskRepository(),
                "roadmap": RoadmapRepository(),
                "milestone": MilestoneRepository(),
                # ... 其他 Repository
            }
            if entity_type_str not in repo_map:
                # Use the enum value for a more robust error message if needed
                raise DatabaseError(f"未为实体类型 '{entity_type_str}' (Enum: {entity_type_enum}) 配置 Repository")

            selected_repo = repo_map[entity_type_str]

            entity_dict = None
            with session_scope() as session:
                logger.debug(f"使用 Repository '{selected_repo.__class__.__name__}' 获取实体 {entity_id}")
                entity_orm = selected_repo.get_by_id(session, entity_id)

                if entity_orm:
                    if show_detail:  # 如果请求了详细信息 (递归)
                        if hasattr(entity_orm, "to_dict"):
                            entity_dict = entity_orm.to_dict()
                            logger.info(f"详细模式：加载实体 {entity_id} 的完整结构")
                        else:
                            # 如果需要详细信息但没有 to_dict，回退到非递归
                            entity_dict = {}
                            for col in entity_orm.__table__.columns:
                                attr_value = getattr(entity_orm, col.name, None)
                                if not isinstance(attr_value, InstrumentedList):
                                    entity_dict[col.name] = attr_value
                            logger.warning(f"请求详细信息，但实体类型 '{entity_type_str}' 的 ORM 对象没有 to_dict 方法，使用非递归基本转换")
                    else:  # 默认情况 (非递归)
                        entity_dict = {}
                        for col in entity_orm.__table__.columns:
                            attr_value = getattr(entity_orm, col.name, None)
                            # 检查属性是否是 SQLAlchemy 的关系列表，如果是则跳过
                            if not isinstance(attr_value, InstrumentedList):
                                entity_dict[col.name] = attr_value
                        logger.info(f"默认模式：仅加载实体 {entity_id} 的顶层字段")
                # else: entity_dict 保持 None
                # session_scope 自动处理

            if not entity_dict:
                console.print(f"[yellow]未找到 {entity_type_str} 类型，ID为 {entity_id} 的条目[/yellow]")
                return 1

            # 始终使用YAML格式输出
            print(yaml.dump(entity_dict, allow_unicode=True, sort_keys=False, default_flow_style=False))  # Use block style YAML
            return 0

        except ValidationError as e:
            logger.error(f"参数验证失败: {e}")
            self.error_handler(e)
            return 1
        except (DatabaseError, KeyError) as e:  # KeyError might happen if entity_type_str is not in repo_map after validation (shouldn't happen)
            logger.error(f"数据库或配置错误: {e}")
            self.error_handler(DatabaseError(f"处理显示命令时出错: {e}"))
            return 1
        except AttributeError as e:  # Catch potential errors if attributes don't exist when non_recursive
            logger.error(f"访问实体属性时出错: {e}", exc_info=True)
            self.error_handler(DatabaseError(f"访问实体属性时出错: {e}"))
            return 1
        except Exception as e:
            logger.error(f"处理显示命令时发生意外错误: {e}", exc_info=True)
            self.error_handler(e)  # Use the generic error handler
            return 1

    def _display_task_details(self, task: Dict) -> None:
        """显示任务详情"""
        # This method seems unused if YAML is always the output format.
        # Consider removing or adapting if table output is needed elsewhere.
        basic_table = Table(show_header=False, box=None)
        basic_table.add_column("字段", style="cyan")
        basic_table.add_column("值")

        fields = [
            ("标题", "title"),
            ("状态", "status"),
            ("优先级", "priority"),
            ("里程碑", "milestone"),
            ("故事ID", "story_id"),
            ("史诗", "epic"),
            ("负责人", "assignee"),
            ("预估工时", "estimate"),
            ("创建时间", "created_at"),
            ("更新时间", "updated_at"),
        ]

        for label, key in fields:
            if key in task:
                value = task[key]
                if value is not None:
                    basic_table.add_row(label, str(value))

        console.print(basic_table)

        if "description" in task and task["description"]:
            console.print("\n[bold]描述:[/bold]")
            console.print(task["description"])

    def _display_epic_details(self, epic: Dict) -> None:
        """显示史诗详情"""
        # This method seems unused if YAML is always the output format.
        basic_table = Table(show_header=False, box=None)
        basic_table.add_column("字段", style="cyan")
        basic_table.add_column("值")

        fields = [
            ("标题", "title"),
            ("状态", "status"),
            ("负责人", "owner"),
            ("创建时间", "created_at"),
            ("更新时间", "updated_at"),
        ]

        for label, key in fields:
            if key in epic:
                value = epic[key]
                if value is not None:
                    basic_table.add_row(label, str(value))

        console.print(basic_table)

        if "description" in epic and epic["description"]:
            console.print("\n[bold]描述:[/bold]")
            console.print(epic["description"])

        if "tasks" in epic and epic["tasks"]:
            console.print("\n[bold]关联任务:[/bold]")
            tasks_table = Table()
            tasks_table.add_column("ID", style="cyan")
            tasks_table.add_column("标题")
            tasks_table.add_column("状态", style="green")

            for task in epic["tasks"]:
                task_id = task["id"] if isinstance(task, dict) else task
                task_title = task.get("title", "未知") if isinstance(task, dict) else "未知"
                task_status = task.get("status", "未知") if isinstance(task, dict) else "未知"
                tasks_table.add_row(str(task_id), task_title, task_status)

            console.print(tasks_table)

    def _display_story_details(self, story: Dict) -> None:
        """显示故事详情"""
        # This method seems unused if YAML is always the output format.
        basic_table = Table(show_header=False, box=None)
        basic_table.add_column("字段", style="cyan")
        basic_table.add_column("值")

        fields = [
            ("标题", "title"),
            ("状态", "status"),
            ("史诗ID", "epic_id"),
            ("负责人", "owner"),
            ("创建时间", "created_at"),
            ("更新时间", "updated_at"),
        ]

        for label, key in fields:
            if key in story:
                value = story[key]
                if value is not None:
                    basic_table.add_row(label, str(value))

        console.print(basic_table)

        if "description" in story and story["description"]:
            console.print("\n[bold]描述:[/bold]")
            console.print(story["description"])

        if "tasks" in story and story["tasks"]:
            console.print("\n[bold]关联任务:[/bold]")
            tasks_table = Table()
            tasks_table.add_column("ID", style="cyan")
            tasks_table.add_column("标题")
            tasks_table.add_column("状态", style="green")

            for task in story["tasks"]:
                task_id = task["id"] if isinstance(task, dict) else task
                task_title = task.get("title", "未知") if isinstance(task, dict) else "未知"
                task_status = task.get("status", "未知") if isinstance(task, dict) else "未知"
                tasks_table.add_row(str(task_id), task_title, task_status)

            console.print(tasks_table)

    def _display_generic_details(self, entity: Dict) -> None:
        """显示通用实体详情"""
        # This method seems unused if YAML is always the output format.
        table = Table(show_header=False, box=None)
        table.add_column("字段", style="cyan")
        table.add_column("值")

        for key, value in entity.items():
            if key != "id":  # ID已在标题显示
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                elif value is None:
                    value = ""
                table.add_row(key, str(value))

        console.print(table)

    def error_handler(self, error: Exception) -> None:
        """
        处理显示命令错误

        Args:
            error: 捕获的异常
        """
        if isinstance(error, (ValidationError, DatabaseError)):
            console.print(f"[red]{str(error)}[/red]")
        else:
            super().error_handler(error)


# 将命令定义移到这里
@click.command(name="show", help="显示数据库条目")
@click.argument("entity_id", required=False)
@click.option("-i", "--id", help="实体ID")
# 修改：将 --non-recursive 改为 -d, --detail
@click.option("-d", "--detail", is_flag=True, help="显示完整的递归数据，包括关联项")
def show_db_cli(entity_id, id: str, detail: bool):  # 参数名改为 detail
    """显示数据库条目的Click命令入口"""
    # 优先使用位置参数，如果没有则使用--id选项
    final_id = entity_id or id

    if not final_id:
        console.print("[red]错误: 请提供要显示的实体ID[/red]", err=True)
        raise click.Abort()

    handler = ShowHandler()
    # 将 detail 标志传递给 handle 方法
    params: Dict[str, Any] = {"id": final_id, "format": "yaml", "detail": detail}  # 使用 detail 替代 non_recursive
    try:
        # handle method now returns 0 for success, 1 for failure
        exit_code = handler.handle(**params)
        if exit_code != 0:
            # Abort if handler indicated failure (e.g., not found)
            # Error message should have been printed by the handler
            raise click.Abort()

    except Exception as e:
        # Error should have been logged by handler, but print a generic message here too
        # The handler itself raises click.Abort on error now, so this might be less likely to hit unless handle fails unexpectedly
        console.print(f"[red]显示条目时发生意外错误: {str(e)}[/red]")
        # Log again just in case it didn't happen in the handler
        logger.error(f"显示条目时发生顶层错误 (ID={final_id}): {e}", exc_info=True)
        raise click.Abort()
