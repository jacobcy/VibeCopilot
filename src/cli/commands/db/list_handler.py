"""
数据库列表处理模块

列出数据库实体
"""

import json
import logging
from typing import Dict, List

from rich.console import Console
from rich.table import Table

from src.cli.commands.db.base import BaseDatabaseCommand

logger = logging.getLogger(__name__)


class ListHandler(BaseDatabaseCommand):
    """数据库列表处理器"""

    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self.console = Console()

    def handle(self, args: Dict) -> int:
        """处理列表命令

        Args:
            args: 命令参数

        Returns:
            执行结果代码
        """
        entity_type = args.get("type")
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")

        if verbose:
            self.console.print(f"列出所有 {entity_type}")

        try:
            # 使用数据库服务获取实体列表
            if not self.db_service:
                logger.error("数据库服务未初始化")
                self.console.print("[red]错误: 数据库服务未初始化[/red]")
                return 1

            entities = self.db_service.get_entities(entity_type)

            # 格式化并显示实体列表
            return self._format_and_display_entities(entities, entity_type, output_format)

        except Exception as e:
            logger.error(f"列出 {entity_type} 失败: {e}")
            self.console.print(f"[red]列出 {entity_type} 失败: {e}[/red]")
            return 1

    def _format_and_display_entities(
        self, entities: List[Dict], entity_type: str, output_format: str
    ) -> int:
        """格式化并显示实体列表

        Args:
            entities: 实体列表
            entity_type: 实体类型
            output_format: 输出格式

        Returns:
            执行结果代码
        """
        if not entities:
            self.console.print(f"[yellow]未找到 {entity_type} 类型的条目[/yellow]")
            return 0

        if output_format == "json":
            # JSON输出
            print(json.dumps(entities, indent=2, ensure_ascii=False))
        else:
            # 表格输出
            if entity_type == "task":
                self._display_task_table(entities)
            elif entity_type == "epic":
                self._display_epic_table(entities)
            elif entity_type == "story":
                self._display_story_table(entities)
            else:
                self._display_generic_table(entities, entity_type)

        return 0

    def _display_task_table(self, tasks: List[Dict]) -> None:
        """显示任务表格

        Args:
            tasks: 任务列表
        """
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

        self.console.print(table)

    def _display_epic_table(self, epics: List[Dict]) -> None:
        """显示史诗表格

        Args:
            epics: 史诗列表
        """
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

        self.console.print(table)

    def _display_story_table(self, stories: List[Dict]) -> None:
        """显示故事表格

        Args:
            stories: 故事列表
        """
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

        self.console.print(table)

    def _display_generic_table(self, entities: List[Dict], entity_type: str) -> None:
        """显示通用表格

        Args:
            entities: 实体列表
            entity_type: 实体类型
        """
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

        self.console.print(table)
