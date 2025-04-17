"""
删除任务命令模块
"""

import logging
from typing import Any, Dict

import click
from rich.console import Console

from src.db.session_manager import session_scope
from src.services.task.core import TaskService

logger = logging.getLogger(__name__)
console = Console()


@click.command(name="delete", help="删除指定的任务")
@click.argument("task_id")
@click.option("--force", "-f", is_flag=True, help="强制删除，不需要确认")
def delete_task(task_id: str, force: bool = False) -> int:
    """
    删除指定的任务。

    默认情况下，该命令会要求确认删除操作。
    使用--force选项可以跳过确认步骤直接删除。

    参数:
        task_id: 要删除的任务ID
        force: 是否强制删除，不需要确认 (默认为False)
    """
    try:
        # 如果不是强制模式，需要用户确认
        if not force:
            confirm = click.confirm(f"确定要删除任务 {task_id} 吗?", default=False)
            if not confirm:
                console.print("[yellow]操作已取消[/yellow]")
                return 0

        # 调用核心逻辑执行删除
        result = execute_delete_task(task_id=task_id)

        # 处理执行结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"删除任务时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


def execute_delete_task(task_id: str) -> Dict[str, Any]:
    """执行删除任务的核心逻辑"""
    logger.info(f"执行删除任务命令: task_id={task_id}")

    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None,
        "meta": {
            "command": "task delete",
            "args": {"task_id": task_id},
        },
    }

    try:
        # --- Database Operations within session_scope ---
        with session_scope() as session:
            task_service = TaskService()

            # Check if task exists (read operation)
            task = task_service.get_task(session, task_id)
            if not task:
                results["status"] = "error"
                results["code"] = 404
                results["message"] = f"删除失败：未找到 Task ID: {task_id}"
                # Return early, no rollback needed for read fail
                return results

            # Perform delete operation
            deleted = task_service.delete_task(session, task_id)
            if deleted:
                results["message"] = f"成功删除任务 {task_id}"
            else:
                # If delete_task returns False, it means deletion failed within the service
                # session_scope will handle rollback if an exception was raised there.
                # If it returned False without exception, set error status here.
                results["status"] = "error"
                results["code"] = 500
                results["message"] = f"删除任务 {task_id} 失败 (服务层返回失败)"
                # Optionally raise an exception here to ensure rollback if delete_task
                # returning False implies a state inconsistency.
                # raise Exception(f"delete_task service call failed for {task_id}")

    except Exception as e:
        # Errors within session_scope or during service calls will trigger rollback
        logger.error(f"删除任务数据库操作期间出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"删除任务时出错: {e}"
        # Error message printing is handled by the caller command

    return results
