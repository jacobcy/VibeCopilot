# src/cli/commands/task/core/show.py

import logging
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)
console = Console()


@click.command(name="show", help="显示任务详情")
@click.argument("task_id", required=False)
@click.option("--verbose", "-v", is_flag=True, help="显示更详细的信息，包括评论")
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml", help="输出格式")
def show_task(task_id: Optional[str] = None, verbose: bool = False, format: str = "yaml") -> None:
    """显示指定任务的详细信息，包括基本信息、描述、关联信息等。

    如果不指定任务ID，则显示当前任务的详情。
    使用 --verbose 选项可以同时显示任务的评论历史。
    """
    try:
        # 执行显示任务详情的逻辑
        result = execute_show_task(task_id=task_id, verbose=verbose, format=format)

        # 处理执行结果
        if result["status"] == "success":
            if not result.get("data"):
                if task_id:
                    console.print(f"[bold red]错误:[/bold red] 找不到任务: {task_id}")
                else:
                    console.print(f"[bold red]错误:[/bold red] 当前没有设置任务")
                return 1

            # 输出任务详情 - 使用task_click模块的format_output函数
            from src.cli.commands.task.task_click import format_output

            print(format_output(result["data"], format=format, verbose=verbose))
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        if verbose:
            logger.error(f"显示任务详情时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


def execute_show_task(
    task_id: Optional[str] = None,
    verbose: bool = False,
    format: str = "yaml",
) -> Dict[str, Any]:
    """执行显示任务详情的核心逻辑

    如果task_id为None，则显示当前任务的详情
    """
    if task_id:
        logger.info(f"执行显示任务命令: task_id={task_id}, verbose={verbose}")
    else:
        logger.info(f"执行显示当前任务命令: verbose={verbose}")

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

            # 如果没有指定任务ID，获取当前任务
            if not task_id:
                from src.services.task import TaskService

                task_service = TaskService()
                current_task = task_service.get_current_task()
                if current_task:
                    task_id = current_task.get("id")
                    logger.info(f"获取到当前任务: {task_id}")
                else:
                    results["status"] = "error"
                    results["code"] = 404
                    results["message"] = "当前没有设置任务"
                    console.print("[bold red]错误:[/bold red] 当前没有设置任务")
                    return results

            # 使用 get_by_id_with_comments 获取任务和评论
            task = task_repo.get_by_id_with_comments(task_id)

            if not task:
                results["status"] = "error"
                results["code"] = 404
                results["message"] = f"未找到 Task ID: {task_id}"
                console.print(f"[bold red]错误:[/bold red] 未找到 Task ID: {task_id}")
                return results

            task_dict = task.to_dict()
            # 将关联的对象 ID 加入字典，方便 agent 使用
            # 使用 getattr 安全地获取属性，如果不存在则返回 None
            task_dict["roadmap_item_id"] = getattr(task, "roadmap_item_id", None) or task.story_id
            task_dict["workflow_session_id"] = getattr(task, "workflow_session_id", None) or getattr(task, "current_session_id", None)
            task_dict["workflow_stage_instance_id"] = getattr(task, "workflow_stage_instance_id", None)
            task_dict["comments"] = [comment.to_dict() for comment in getattr(task, "comments", [])]

            results["data"] = task_dict
            results["message"] = f"成功检索到任务 {task_id}"

            # --- 控制台输出 ---
            # 基本信息表格
            table = Table(title=f"任务详情: {task.title} (ID: {task.id[:8]})", show_header=False, box=None)
            table.add_column("Field", style="bold blue")
            table.add_column("Value")

            table.add_row("ID", task.id)
            table.add_row("状态", task.status)
            table.add_row("负责人", task.assignee if task.assignee else "-")
            table.add_row("标签", ", ".join(task.labels) if task.labels else "-")

            # 安全获取时间字段
            created_at = getattr(task, "created_at", None)
            if isinstance(created_at, str):
                created_at_str = created_at
            elif hasattr(created_at, "strftime"):
                created_at_str = created_at.strftime("%Y-%m-%d %H:%M")
            else:
                created_at_str = "-"

            updated_at = getattr(task, "updated_at", None)
            if isinstance(updated_at, str):
                updated_at_str = updated_at
            elif hasattr(updated_at, "strftime"):
                updated_at_str = updated_at.strftime("%Y-%m-%d %H:%M")
            else:
                updated_at_str = "-"

            table.add_row("创建时间", created_at_str)
            table.add_row("更新时间", updated_at_str)

            closed_at = getattr(task, "closed_at", None)
            if closed_at:
                if isinstance(closed_at, str):
                    closed_at_str = closed_at
                elif hasattr(closed_at, "strftime"):
                    closed_at_str = closed_at.strftime("%Y-%m-%d %H:%M")
                else:
                    closed_at_str = str(closed_at)
                table.add_row("关闭时间", closed_at_str)

            # 关联信息
            story_id = getattr(task, "story_id", None)
            table.add_row("关联 Story", story_id if story_id else "-")

            # 显示工作流会话ID（如果有）
            current_session_id = getattr(task, "current_session_id", None)
            if current_session_id:
                table.add_row("关联工作流会话", current_session_id)

            # 检查是否是当前任务
            is_current = getattr(task, "is_current", None)
            if is_current:
                table.add_row("当前任务", "是")

            github_issue = getattr(task, "github_issue", None)
            if github_issue:
                table.add_row("关联 GitHub Issue", github_issue)

            github_issue_number = getattr(task, "github_issue_number", None)
            if github_issue_number:
                # 假设未来有方法获取 repo 信息
                repo_placeholder = "owner/repo"  # 需要从某处获取
                github_url = f"https://github.com/{repo_placeholder}/issues/{github_issue_number}"
                link_text = f"[{repo_placeholder}#{github_issue_number}]({github_url})"
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
        console.print(f"[bold red]错误:[/bold red] {e}")

    return results
