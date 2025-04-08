# src/cli/commands/task/task_show_command.py

import argparse
import logging
from typing import Any, Dict, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.cli.commands.base_command import BaseCommand
from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)
console = Console()


class ShowTaskCommand(BaseCommand):
    """显示任务详情命令

    显示指定任务的详细信息，包括基本信息、描述、关联信息等。
    使用 --verbose 选项可以同时显示任务的评论历史。

    参数:
        task_id: 要显示的任务 ID

    选项:
        --verbose, -v: 显示更详细的信息，包括评论
    """

    def __init__(self):
        super().__init__("show", "显示指定任务的详细信息")

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """配置命令行解析器"""
        parser.add_argument("task_id", help="要显示的 Task ID")
        parser.add_argument("-v", "--verbose", action="store_true", help="显示更详细的信息，包括评论")

    def execute_with_args(self, args: argparse.Namespace) -> int:
        """执行命令"""
        try:
            self.execute(
                task_id=args.task_id,
                verbose=args.verbose,
            )
            return 0
        except Exception as e:
            logger.error(f"显示任务详情时出错: {e}", exc_info=True)
            console.print(f"[bold red]错误:[/bold red] {e}")
            return 1

    def execute(
        self,
        task_id: str,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """执行显示任务详情的逻辑"""
        logger.info(f"执行显示任务命令: task_id={task_id}, verbose={verbose}")

        results = {
            "status": "success",
            "code": 0,
            "message": "",
            "data": None,
            "meta": {"command": "task show", "args": {"task_id": task_id, "verbose": verbose}},
        }

        try:
            session_factory = get_session_factory()
            with session_factory() as session:
                task_repo = TaskRepository(session)
                # 使用 get_by_id_with_comments 获取任务和评论
                task = task_repo.get_by_id_with_comments(task_id)

                if not task:
                    results["status"] = "error"
                    results["code"] = 404
                    results["message"] = f"未找到 Task ID: {task_id}"
                    if not self.is_agent_mode(locals()):
                        console.print(f"[bold red]错误:[/bold red] 未找到 Task ID: {task_id}")
                    return results

                task_dict = task.to_dict()
                # 将关联的对象 ID 加入字典，方便 agent 使用
                task_dict["roadmap_item_id"] = task.roadmap_item_id
                task_dict["workflow_session_id"] = task.workflow_session_id
                task_dict["workflow_stage_instance_id"] = task.workflow_stage_instance_id
                task_dict["comments"] = [comment.to_dict() for comment in task.comments]

                results["data"] = task_dict
                results["message"] = f"成功检索到任务 {task_id}"

                # --- 控制台输出 (非 Agent 模式) ---
                if not self.is_agent_mode(locals()):
                    # 基本信息表格
                    table = Table(title=f"任务详情: {task.title} (ID: {task.id[:8]})", show_header=False, box=None)
                    table.add_column("Field", style="bold blue")
                    table.add_column("Value")

                    table.add_row("ID", task.id)
                    table.add_row("状态", task.status)
                    table.add_row("负责人", task.assignee if task.assignee else "-")
                    table.add_row("标签", ", ".join(task.labels) if task.labels else "-")
                    table.add_row(
                        "创建时间",
                        task.created_at.strftime("%Y-%m-%d %H:%M") if task.created_at else "-",
                    )
                    table.add_row(
                        "更新时间",
                        task.updated_at.strftime("%Y-%m-%d %H:%M") if task.updated_at else "-",
                    )
                    if task.closed_at:
                        table.add_row("关闭时间", task.closed_at.strftime("%Y-%m-%d %H:%M"))

                    # 关联信息
                    table.add_row("关联 Story", task.roadmap_item_id if task.roadmap_item_id else "-")
                    if task.github_issue_number:
                        # 假设未来有方法获取 repo 信息
                        repo_placeholder = "owner/repo"  # 需要从某处获取
                        github_url = f"https://github.com/{repo_placeholder}/issues/{task.github_issue_number}"
                        link_text = f"[{repo_placeholder}#{task.github_issue_number}]({github_url})"
                        table.add_row(
                            "关联 GitHub Issue",
                            link_text,
                        )

                    console.print(table)

                    # 描述
                    if task.description:
                        console.print(Panel(Markdown(task.description), title="描述", border_style="dim"))
                    else:
                        console.print(Panel("[dim]无描述[/dim]", title="描述", border_style="dim"))

                    # 评论 (如果 verbose)
                    if verbose and task.comments:
                        console.print("\n[bold underline]评论:[/bold underline]")
                        for comment in task.comments:
                            comment_panel = Panel(
                                Markdown(comment.content),
                                title=f"评论者: {comment.author or '匿名'} @ {comment.created_at.strftime('%Y-%m-%d %H:%M')}",
                                border_style="cyan",
                                title_align="left",
                            )
                            console.print(comment_panel)
                    elif verbose:
                        console.print("\n[dim]无评论[/dim]")

        except Exception as e:
            logger.error(f"显示任务详情时出错: {e}", exc_info=True)
            results["status"] = "error"
            results["code"] = 500
            results["message"] = f"显示任务详情时出错: {e}"
            if not self.is_agent_mode(locals()):
                console.print(f"[bold red]错误:[/bold red] {e}")

        return results

    def is_agent_mode(self, args: Dict[str, Any]) -> bool:
        """检查是否处于 Agent 模式 (简化)"""
        return False
