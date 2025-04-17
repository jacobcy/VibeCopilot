"""
添加任务评论命令模块
"""

import logging
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.db.session_manager import session_scope
from src.services.task.core import TaskService

logger = logging.getLogger(__name__)
console = Console()


@click.command(name="comment", help="添加任务评论")
@click.argument("task_id")
@click.option("--comment", "-c", required=True, help="要添加的评论")
@click.option("--author", "-a", help="评论作者")
def comment_task(task_id: str, comment: str, author: Optional[str] = None) -> int:
    """为指定的任务添加评论。

    评论支持Markdown格式，可以包含富文本内容。
    评论将按时间顺序保存，并可以通过task show命令查看。

    参数:
        task_id: 要评论的任务ID
        comment: 评论内容 (必需，支持Markdown格式)
        author: 评论者名称 (可选，默认为当前用户或系统)
    """
    try:
        # 调用核心逻辑
        result = execute_comment_task(task_id=task_id, content=comment, author=author)

        # 处理执行结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            if result.get("data"):
                # 显示评论预览
                comment_data = result["data"]
                comment_panel = Panel(
                    Markdown(comment_data.get("content", "")),
                    title=f"评论者: {comment_data.get('author', '匿名')} @ {comment_data.get('created_at', '')}",
                    border_style="cyan",
                    title_align="left",
                )
                console.print(comment_panel)
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"添加评论时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


def execute_comment_task(
    task_id: str,
    content: str,
    author: Optional[str] = None,
) -> Dict[str, Any]:
    """执行添加任务评论的核心逻辑"""
    logger.info(f"执行添加评论命令: task_id={task_id}, author={author}")

    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None,
        "meta": {
            "command": "task comment",
            "args": {"task_id": task_id, "author": author},
        },
    }

    if not content or content.isspace():
        results["status"] = "error"
        results["code"] = 400
        results["message"] = "评论内容不能为空。"
        console.print("[bold red]错误:[/bold red] 评论内容不能为空。")
        return results

    try:
        # --- Database Operations within session_scope ---
        with session_scope() as session:
            task_service = TaskService()

            # Check if task exists (read operation)
            task = task_service.get_task(session, task_id)
            if not task:
                results["status"] = "error"
                results["code"] = 404
                results["message"] = f"添加评论失败：未找到 Task ID: {task_id}"
                # No console print here, handled by caller
                return results

            # Add comment
            comment_dict = task_service.add_task_comment(session, task_id=task_id, comment=content, author=author)
            if comment_dict:
                results["data"] = comment_dict
                results["message"] = f"成功为任务 {task_id} 添加评论 (ID: {comment_dict.get('id')})"
            else:
                # If add_task_comment returns None/False, implies failure
                results["status"] = "error"
                results["code"] = 500
                results["message"] = "添加评论失败 (服务层返回失败)"
                # Optionally raise an exception here to ensure rollback
                # raise Exception(f"add_task_comment service call failed for {task_id}")

    except Exception as e:
        # Errors within session_scope or during service calls will trigger rollback
        logger.error(f"添加评论数据库操作期间出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"添加评论时出错: {e}"
        # Error message printing is handled by the caller command

    return results
