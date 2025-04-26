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

from src.db.repositories.roadmap_repository import EpicRepository, MilestoneRepository, RoadmapRepository, StoryRepository
from src.db.repositories.task_repository import TaskRepository
from src.db.session_manager import session_scope
from src.utils.id_generator import IdGenerator

from .base_handler import ClickBaseHandler
from .exceptions import DatabaseError, ValidationError
from .validators import validate_db_name

logger = logging.getLogger(__name__)
console = Console()


class ShowHandler(ClickBaseHandler):
    """数据库条目显示命令处理器"""

    VALID_FORMATS = {"table", "json", "yaml"}

    def __init__(self):
        super().__init__()

    def validate(self, **kwargs: Dict[str, Any]) -> bool:
        """
        验证显示命令参数

        Args:
            **kwargs: 命令参数 (只需要 id 和 format)

        Returns:
            bool: 验证是否通过

        Raises:
            ValidationError: 验证失败时抛出
        """
        entity_id = kwargs.get("id")
        output_format = kwargs.get("format", "table")

        if not entity_id:
            raise ValidationError("实体ID不能为空")

        try:
            entity_type_enum = IdGenerator.get_entity_type_from_id(entity_id)
            if entity_type_enum is None:
                raise ValidationError(f"无法从ID '{entity_id}' 推断出有效的实体类型")
        except ValueError as e:
            raise ValidationError(f"无效的实体ID格式: {entity_id}. {str(e)}")

        if output_format not in self.VALID_FORMATS:
            raise ValidationError(f"不支持的输出格式: {output_format}")

        return True

    def handle(self, **kwargs: Dict[str, Any]) -> int:
        entity_id = kwargs.get("id")
        output_format = kwargs.get("format", "table")

        try:
            self.validate(id=entity_id, format=output_format)
            entity_type_enum = IdGenerator.get_entity_type_from_id(entity_id)
            entity_type_str = entity_type_enum.name.lower()

            logger.info(f"尝试显示类型 '{entity_type_str}' 的实体，ID: {entity_id}")

            repo_map = {
                "epic": EpicRepository(),
                "story": StoryRepository(),
                "task": TaskRepository(),
                "roadmap": RoadmapRepository(),
                "milestone": MilestoneRepository(),
            }
            if entity_type_str not in repo_map:
                raise DatabaseError(f"未为实体类型 '{entity_type_str}' 配置 Repository")

            selected_repo = repo_map[entity_type_str]

            entity_dict = None
            with session_scope() as session:
                logger.debug(f"使用 Repository '{selected_repo.__class__.__name__}' 获取实体 {entity_id}")
                entity_orm = selected_repo.get_by_id(session, entity_id)

                if entity_orm:
                    if hasattr(entity_orm, "to_dict"):
                        entity_dict = entity_orm.to_dict()
                    else:
                        entity_dict = {col.name: getattr(entity_orm, col.name) for col in entity_orm.__table__.columns}
                        logger.warning(f"实体类型 '{entity_type_str}' 的 ORM 对象没有 to_dict 方法，使用基本转换")
                # else: entity_dict 保持 None
                # session_scope 自动处理

            if not entity_dict:
                console.print(f"[yellow]未找到 {entity_type_str} 类型，ID为 {entity_id} 的条目[/yellow]")
                return 1

            return self._display_entity(entity_dict, entity_type_str, entity_id, output_format)

        except ValidationError as e:
            logger.error(f"参数验证失败: {e}")
            self.error_handler(e)
            return 1
        except (DatabaseError, KeyError) as e:
            logger.error(f"数据库或配置错误: {e}")
            self.error_handler(DatabaseError(f"处理显示命令时出错: {e}"))
            return 1
        except Exception as e:
            logger.error(f"处理显示命令时发生意外错误: {e}", exc_info=True)
            self.error_handler(e)
            return 1

    def _display_entity(self, entity: Dict, entity_type: str, entity_id: str, output_format: str) -> int:
        """显示实体详情"""
        if output_format == "json":
            print(json.dumps(entity, indent=2, ensure_ascii=False))
        elif output_format == "yaml":
            print(yaml.dump(entity, allow_unicode=True, sort_keys=False))
        else:
            console.print(f"[bold]{entity_type} (ID: {entity_id})[/bold]")
            display_method = getattr(self, f"_display_{entity_type}_details", self._display_generic_details)
            display_method(entity)

        return 0

    def _display_task_details(self, task: Dict) -> None:
        """显示任务详情"""
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
