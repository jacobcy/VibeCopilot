# src/cli/commands/task/task_comment_command.py

import logging
from typing import Any, Dict, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.cli.commands.base_command import BaseCommand
from src.db import get_session_factory
from src.db.repositories.task_repository import TaskCommentRepository, TaskRepository  # TaskRepository needed to check if task exists

logger = logging.getLogger(__name__)
console = Console()


class CommentTaskCommand(BaseCommand):
    """添加任务评论命令

    为指定的任务添加评论。评论支持Markdown格式，可以包含富文本内容。
    评论将按时间顺序保存，并可以通过task show命令查看。

    参数:
        task_id: 要评论的任务ID

    选项:
        --content, -c: 评论内容 (必需，支持Markdown格式)
        --author, -a: 评论者名称 (可选，默认为当前用户或系统)

    示例:
        vibecopilot task comment abc123 -c "修复了问题" -a "开发者"
        vibecopilot task comment def456 --content "# 更新进度\n- 完成功能A\n- 测试通过"
    """

    def __init__(self):
        super().__init__("comment", "为指定的任务添加评论")

    def execute(
        self,
        task_id: str = typer.Argument(..., help="要评论的 Task ID"),
        content: str = typer.Option(..., "--content", "-c", help="评论内容 (必需)"),
        author: Optional[str] = typer.Option(None, "--author", "-a", help="评论者 (默认为当前用户或系统)"),
    ) -> Dict[str, Any]:
        """执行添加任务评论的逻辑"""
        logger.info(f"执行添加评论命令: task_id={task_id}, author={author}")

        results = {
            "status": "success",
            "code": 0,
            "message": "",
            "data": None,
            "meta": {
                "command": "task comment",
                "args": {"task_id": task_id, "author": author},
            },  # Exclude content from meta args for brevity/privacy
        }

        if not content or content.isspace():
            results["status"] = "error"
            results["code"] = 400
            results["message"] = "评论内容不能为空。"
            if not self.is_agent_mode(locals()):
                console.print("[bold red]错误:[/bold red] 评论内容不能为空。")
            return results

        try:
            session_factory = get_session_factory()
            with session_factory() as session:
                task_repo = TaskRepository(session)
                comment_repo = TaskCommentRepository(session)

                # 检查任务是否存在
                task = task_repo.get_by_id(task_id)
                if not task:
                    results["status"] = "error"
                    results["code"] = 404
                    results["message"] = f"添加评论失败：未找到 Task ID: {task_id}"
                    if not self.is_agent_mode(locals()):
                        console.print(f"[bold red]错误:[/bold red] 未找到 Task ID: {task_id}")
                    return results

                # 添加评论
                new_comment = comment_repo.add_comment(task_id=task_id, content=content, author=author)
                session.commit()  # 提交评论

                comment_dict = new_comment.to_dict()
                results["data"] = comment_dict
                results["message"] = f"成功为任务 {task_id} 添加评论 (ID: {new_comment.id})"

                # --- 控制台输出 (非 Agent 模式) ---
                if not self.is_agent_mode(locals()):
                    console.print(f"[bold green]成功:[/bold green] 已为任务 {task_id} 添加评论。")
                    comment_panel = Panel(
                        Markdown(new_comment.content),
                        title=f"评论者: {new_comment.author or '匿名'} @ {new_comment.created_at.strftime('%Y-%m-%d %H:%M')}",
                        border_style="cyan",
                        title_align="left",
                    )
                    console.print(comment_panel)

        except Exception as e:
            logger.error(f"添加评论时出错: {e}", exc_info=True)
            results["status"] = "error"
            results["code"] = 500
            results["message"] = f"添加评论时出错: {e}"
            console.print(f"[bold red]错误:[/bold red] {e}")

        return results

    def is_agent_mode(self, args: Dict[str, Any]) -> bool:
        """检查是否处于 Agent 模式 (简化)"""
        return False
