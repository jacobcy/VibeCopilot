"""
删除任务命令模块
"""

import logging
from typing import Any, Dict

import click
from rich.console import Console

# 移除不再需要的 session_scope
# from src.db.session_manager import session_scope
from src.services.task.core import TaskService

logger = logging.getLogger(__name__)
console = Console()


@click.command(name="delete", help="删除指定的任务 (可通过ID或标题)")
@click.argument("identifier")
@click.option("--force", "-f", is_flag=True, help="强制删除，不需要确认")
def delete_task(identifier: str, force: bool = False) -> int:
    """
    删除指定的任务。

    可以通过任务ID或任务标题来指定要删除的任务。
    默认情况下，该命令会要求确认删除操作。
    使用--force选项可以跳过确认步骤直接删除。

    参数:
        identifier: 要删除的任务ID或标题
        force: 是否强制删除，不需要确认 (默认为False)
    """
    try:
        # 如果不是强制模式，需要用户确认
        if not force:
            # 使用 identifier 显示给用户
            confirm = click.confirm(f"确定要删除任务 {identifier} 吗?", default=False)
            if not confirm:
                console.print("[yellow]操作已取消[/yellow]")
                return 0

        # 调用核心逻辑执行删除，传递 identifier
        result = execute_delete_task(identifier=identifier)

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


def execute_delete_task(identifier: str) -> Dict[str, Any]:
    """执行删除任务的核心逻辑"""
    logger.info(f"执行删除任务命令: identifier={identifier}")

    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None,
        "meta": {
            "command": "task delete",
            "args": {"identifier": identifier},
        },
    }

    try:
        # --- 不再需要 session_scope 和手动检查存在性 ---
        # with session_scope() as session:
        #     task_service = TaskService()
        #     task = task_service.get_task(session, task_id)
        #     if not task:
        #         ...

        # 直接调用 TaskService 的 delete_task
        task_service = TaskService()
        deleted = task_service.delete_task(identifier=identifier)

        if deleted:
            results["message"] = f"成功删除任务 {identifier}"
        else:
            # delete_task 内部应已记录错误，这里设置失败状态
            results["status"] = "error"
            results["code"] = 404  # 假设主要是未找到
            results["message"] = f"删除任务 {identifier} 失败 (未找到或删除时出错)"

    except Exception as e:
        # TaskService.delete_task 内部的异常应已被捕获并记录
        # 这里捕获调用过程本身的异常
        logger.error(f"删除任务执行期间出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"删除任务时发生意外错误: {e}"

    return results
