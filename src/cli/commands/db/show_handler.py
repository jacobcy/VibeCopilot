"""
数据库条目显示模块

显示数据库中的单个实体条目
"""

import json
import logging
from typing import Dict

from rich.console import Console
from rich.table import Table

from src.cli.commands.db.base import BaseDatabaseCommand

logger = logging.getLogger(__name__)


class ShowHandler(BaseDatabaseCommand):
    """数据库条目显示处理器"""

    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self.console = Console()

    def handle(self, args: Dict) -> int:
        """处理显示命令

        Args:
            args: 命令参数

        Returns:
            执行结果代码
        """
        entity_type = args.get("type")
        entity_id = args.get("id")
        output_format = args.get("format", "text")

        try:
            # 使用数据库服务获取实体
            if not self.db_service:
                logger.error("数据库服务未初始化")
                self.console.print("[red]错误: 数据库服务未初始化[/red]")
                return 1

            entity = self.db_service.get_entity(entity_type, entity_id)

            if not entity:
                self.console.print(f"[yellow]未找到 {entity_type} 类型，ID为 {entity_id} 的条目[/yellow]")
                return 1

            if output_format == "json":
                # JSON输出
                print(json.dumps(entity, indent=2, ensure_ascii=False))
            else:
                # 表格输出
                self.console.print(f"[bold]{entity_type} (ID: {entity_id})[/bold]")

                if entity_type == "task":
                    self._display_task_details(entity)
                elif entity_type == "epic":
                    self._display_epic_details(entity)
                elif entity_type == "story":
                    self._display_story_details(entity)
                else:
                    self._display_generic_details(entity)

            return 0

        except Exception as e:
            logger.error(f"显示 {entity_type} {entity_id} 失败: {e}")
            self.console.print(f"[red]显示 {entity_type} {entity_id} 失败: {e}[/red]")
            return 1

    def _display_task_details(self, task: Dict) -> None:
        """显示任务详情

        Args:
            task: 任务数据
        """
        # 基本信息表
        basic_table = Table(show_header=False, box=None)
        basic_table.add_column("字段", style="cyan")
        basic_table.add_column("值")

        # 添加关键字段
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

        self.console.print(basic_table)

        # 显示描述
        if "description" in task and task["description"]:
            self.console.print("\n[bold]描述:[/bold]")
            self.console.print(task["description"])

    def _display_epic_details(self, epic: Dict) -> None:
        """显示史诗详情

        Args:
            epic: 史诗数据
        """
        # 基本信息表
        basic_table = Table(show_header=False, box=None)
        basic_table.add_column("字段", style="cyan")
        basic_table.add_column("值")

        # 添加关键字段
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

        self.console.print(basic_table)

        # 显示描述
        if "description" in epic and epic["description"]:
            self.console.print("\n[bold]描述:[/bold]")
            self.console.print(epic["description"])

        # 显示关联任务
        if "tasks" in epic and epic["tasks"]:
            self.console.print("\n[bold]关联任务:[/bold]")
            tasks_table = Table()
            tasks_table.add_column("ID", style="cyan")
            tasks_table.add_column("标题")
            tasks_table.add_column("状态", style="green")

            for task in epic["tasks"]:
                task_id = task["id"] if isinstance(task, dict) else task
                task_title = task.get("title", "未知") if isinstance(task, dict) else "未知"
                task_status = task.get("status", "未知") if isinstance(task, dict) else "未知"
                tasks_table.add_row(str(task_id), task_title, task_status)

            self.console.print(tasks_table)

    def _display_story_details(self, story: Dict) -> None:
        """显示故事详情

        Args:
            story: 故事数据
        """
        # 基本信息表
        basic_table = Table(show_header=False, box=None)
        basic_table.add_column("字段", style="cyan")
        basic_table.add_column("值")

        # 添加关键字段
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

        self.console.print(basic_table)

        # 显示描述
        if "description" in story and story["description"]:
            self.console.print("\n[bold]描述:[/bold]")
            self.console.print(story["description"])

        # 显示关联任务
        if "tasks" in story and story["tasks"]:
            self.console.print("\n[bold]关联任务:[/bold]")
            tasks_table = Table()
            tasks_table.add_column("ID", style="cyan")
            tasks_table.add_column("标题")
            tasks_table.add_column("状态", style="green")

            for task in story["tasks"]:
                task_id = task["id"] if isinstance(task, dict) else task
                task_title = task.get("title", "未知") if isinstance(task, dict) else "未知"
                task_status = task.get("status", "未知") if isinstance(task, dict) else "未知"
                tasks_table.add_row(str(task_id), task_title, task_status)

            self.console.print(tasks_table)

    def _display_generic_details(self, entity: Dict) -> None:
        """显示通用实体详情

        Args:
            entity: 实体数据
        """
        table = Table(show_header=False, box=None)
        table.add_column("字段", style="cyan")
        table.add_column("值")

        for key, value in entity.items():
            if key != "id":  # ID已在标题显示
                if isinstance(value, dict) or isinstance(value, list):
                    value = json.dumps(value, ensure_ascii=False)
                elif value is None:
                    value = ""
                table.add_row(key, str(value))

        self.console.print(table)
