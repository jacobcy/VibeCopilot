# src/cli/commands/task/task_update_command.py

import argparse
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands.base_command import BaseCommand
from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)
console = Console()


class TaskStatus(str, Enum):
    """任务状态枚举"""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class UpdateTaskCommand(BaseCommand):
    """更新任务命令

    更新现有任务的信息，支持修改标题、描述、负责人、状态等。
    标签更新支持完全替换、添加或移除单个标签。

    参数:
        task_id: 要更新的任务 ID

    选项:
        --title, -t: 新的任务标题
        --desc, -d: 新的任务描述
        --assignee, -a: 新的负责人 ('-' 表示清空)
        --label, -l: 设置新的标签列表 (覆盖旧列表)
        --add-label: 添加标签
        --remove-label: 移除标签
        --status, -s: 新的状态

    注意: 关联信息的更新请使用 'task link' 命令
    """

    def __init__(self):
        super().__init__("update", "更新一个已存在的任务")

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """配置命令行参数解析器

        Args:
            parser: ArgumentParser 实例
        """
        parser.add_argument("task_id", type=str, help="要更新的任务ID")
        parser.add_argument("--title", "-t", type=str, help="新的任务标题")
        parser.add_argument("--description", "-d", type=str, help="新的任务描述")
        parser.add_argument("--assignee", "-a", type=str, help="新的任务负责人")
        parser.add_argument("--status", "-s", type=str, choices=[status.value for status in TaskStatus], help="新的任务状态")
        parser.add_argument("--label", "-l", type=str, action="append", help="设置任务标签(可多次使用)")
        parser.add_argument("--add-label", type=str, action="append", help="添加任务标签(可多次使用)")
        parser.add_argument("--remove-label", type=str, action="append", help="移除任务标签(可多次使用)")
        parser.add_argument("--no-diff", action="store_true", help="不显示任务更新前后的差异")

    def execute_with_args(self, args: argparse.Namespace) -> Dict[str, Any]:
        """使用解析后的参数执行命令"""
        return self.execute(
            task_id=args.task_id,
            title=args.title,
            description=args.description,
            assignee=args.assignee,
            label=args.label,
            add_label=args.add_label,
            remove_label=args.remove_label,
            status=args.status,
            no_diff=args.no_diff,
        )

    def execute(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        label: Optional[List[str]] = None,
        add_label: Optional[List[str]] = None,
        remove_label: Optional[List[str]] = None,
        status: Optional[str] = None,
        no_diff: bool = False,
    ) -> Dict[str, Any]:
        """执行任务更新命令

        Args:
            task_id: 要更新的任务ID
            title: 新的任务标题
            description: 新的任务描述
            assignee: 新的任务负责人
            label: 设置的标签列表
            add_label: 要添加的标签列表
            remove_label: 要移除的标签列表
            status: 新的任务状态
            no_diff: 是否不显示差异

        Returns:
            包含更新结果的字典
        """
        self.logger.info(f"正在更新任务 {task_id}")
        results = {"success": False, "message": "", "data": None}

        try:
            # 1. 获取原始任务
            task = self.task_service.get_task(task_id)
            if not task:
                raise ValueError(f"找不到任务 {task_id}")

            old_task = task.copy()

            # 2. 验证状态
            if status:
                try:
                    TaskStatus(status)  # 验证状态是否有效
                except ValueError:
                    raise ValueError(f"无效的任务状态: {status}")
                task.status = status

            # 3. 更新基本信息
            if title is not None:
                task.title = title
            if description is not None:
                task.description = description
            if assignee is not None:
                task.assignee = assignee if assignee != "-" else ""

            # 4. 处理标签更新
            if label is not None:
                task.labels = set(label)
            else:
                current_labels = set(task.labels or set())
                if add_label:
                    current_labels.update(add_label)
                if remove_label:
                    current_labels.difference_update(remove_label)
                task.labels = current_labels

            # 5. 保存更新
            self.task_service.update_task(task)

            # 6. 显示差异
            if not no_diff:
                table = Table(title="任务更新差异", show_header=True)
                table.add_column("字段", style="cyan")
                table.add_column("原值", style="red")
                table.add_column("新值", style="green")

                for field in ["title", "description", "assignee", "status"]:
                    old_value = getattr(old_task, field) or ""
                    new_value = getattr(task, field) or ""
                    if old_value != new_value:
                        table.add_row(field, str(old_value), str(new_value))

                # 处理标签差异
                old_labels = set(old_task.labels or set())
                new_labels = set(task.labels or set())
                if old_labels != new_labels:
                    table.add_row("labels", ", ".join(sorted(old_labels)) or "-", ", ".join(sorted(new_labels)) or "-")

                self.console.print(Panel(table, title="更新成功"))

            results["success"] = True
            results["message"] = "任务更新成功"
            results["data"] = task

        except ValueError as e:
            self.logger.error(f"更新任务失败: {str(e)}")
            results["message"] = str(e)
        except Exception as e:
            self.logger.error(f"更新任务时发生错误: {str(e)}", exc_info=True)
            results["message"] = f"更新任务时发生错误: {str(e)}"

        return results

    def is_agent_mode(self, args: Dict[str, Any]) -> bool:
        """检查是否处于 Agent 模式 (简化)"""
        return False
