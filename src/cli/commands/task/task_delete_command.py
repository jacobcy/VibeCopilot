# src/cli/commands/task/task_delete_command.py

import argparse
import logging
from typing import Any, Dict

import typer
from rich.console import Console

from src.cli.commands.base_command import BaseCommand
from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)
console = Console()


class DeleteTaskCommand(BaseCommand):
    """删除任务命令

    删除指定的任务。为防止误操作，默认需要使用 --force 选项确认删除。
    删除操作不可逆，请谨慎使用。

    参数:
        task_id: 要删除的任务 ID

    选项:
        --force, -f: 跳过确认直接删除

    注意: 删除操作会同时删除任务的所有关联信息和评论。
    """

    def __init__(self):
        super().__init__("delete", "删除一个指定的任务")

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """配置命令的参数解析器"""
        parser.add_argument("task_id", help="要删除的 Task ID")
        parser.add_argument("-f", "--force", action="store_true", help="跳过确认直接删除")

    def execute_with_args(self, args: argparse.Namespace) -> Dict[str, Any]:
        """使用解析后的参数执行命令"""
        return self.execute(task_id=args.task_id, force=args.force)

    def execute(
        self,
        task_id: str = typer.Argument(..., help="要删除的 Task ID"),
        force: bool = typer.Option(False, "--force", "-f", help="跳过确认直接删除"),
    ) -> Dict[str, Any]:
        """执行删除任务的逻辑"""
        logger.info(f"执行删除任务命令: task_id={task_id}, force={force}")

        results = {
            "status": "success",
            "code": 0,
            "message": "",
            "data": {"task_id": task_id, "deleted": False},
            "meta": {"command": "task delete", "args": {"task_id": task_id, "force": force}},
        }

        # --- 确认逻辑 (非 Agent 模式) ---
        if not force and not self.is_agent_mode(locals()):
            # 在实际应用中，可能需要获取任务标题来提供更好的确认信息
            # confirmed = typer.confirm(f"确定要删除 Task ID: {task_id} 吗?")
            # 这里简化为强制使用 --force
            console.print(f"[bold yellow]警告:[/bold yellow] 删除操作不可逆。请使用 `--force` 选项确认删除 Task ID: {task_id}")
            results["status"] = "aborted"
            results["message"] = "删除操作未确认，已中止。"
            return results
        elif not force and self.is_agent_mode(locals()):
            # Agent 模式下，没有 --force 视为中止
            results["status"] = "aborted"
            results["message"] = "需要 '--force' 选项才能执行删除。"
            return results

        try:
            session_factory = get_session_factory()
            with session_factory() as session:
                task_repo = TaskRepository(session)
                deleted = task_repo.delete(task_id)  # Repository 基类提供 delete 方法

                if deleted:
                    session.commit()  # 提交删除
                    results["data"]["deleted"] = True
                    results["message"] = f"成功删除任务 (ID: {task_id})"
                    if not self.is_agent_mode(locals()):
                        console.print(f"[bold green]成功:[/bold green] 已删除任务 (ID: {task_id})")
                else:
                    results["status"] = "error"
                    results["code"] = 404
                    results["message"] = f"删除失败：未找到 Task ID: {task_id}"
                    if not self.is_agent_mode(locals()):
                        console.print(f"[bold red]错误:[/bold red] 未找到 Task ID: {task_id}")

        except Exception as e:
            logger.error(f"删除任务时出错: {e}", exc_info=True)
            results["status"] = "error"
            results["code"] = 500
            results["message"] = f"删除任务时出错: {e}"
            console.print(f"[bold red]错误:[/bold red] {e}")

        return results

    def is_agent_mode(self, args: Dict[str, Any]) -> bool:
        """检查是否处于 Agent 模式 (简化)"""
        return False
