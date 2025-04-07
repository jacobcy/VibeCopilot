# src/cli/commands/task/task_update_command.py

import logging
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console

from src.cli.commands.base_command import BaseCommand
from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)
console = Console()


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

    def execute(
        self,
        task_id: str = typer.Argument(..., help="要更新的 Task ID"),
        title: Optional[str] = typer.Option(None, "--title", "-t", help="新的任务标题"),
        description: Optional[str] = typer.Option(None, "--desc", "-d", help="新的任务描述"),
        assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="新的负责人 ('-' 表示清空)"),
        label: Optional[List[str]] = typer.Option(None, "--label", "-l", help="设置新的标签列表 (会覆盖旧列表)"),
        add_label: Optional[List[str]] = typer.Option(None, "--add-label", help="添加标签"),
        remove_label: Optional[List[str]] = typer.Option(None, "--remove-label", help="移除标签"),
        status: Optional[str] = typer.Option(None, "--status", "-s", help="新的状态")
        # 关联更新建议通过 'task link' 命令处理，这里保持简单
    ) -> Dict[str, Any]:
        """执行更新任务的逻辑"""
        logger.info(
            f"执行更新任务命令: task_id={task_id}, title='{title}', assignee={assignee}, labels={label}, "
            f"add_labels={add_label}, remove_labels={remove_label}, status={status}"
        )

        results = {
            "status": "success",
            "code": 0,
            "message": "",
            "data": None,
            "meta": {"command": "task update", "args": locals()},
        }

        update_data: Dict[str, Any] = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if assignee is not None:
            # 允许传入 "-" 来清空负责人
            update_data["assignee"] = None if assignee == "-" else assignee
        if status is not None:
            update_data["status"] = status
        # 注意: label, add_label, remove_label 需要特殊处理

        if not update_data and label is None and add_label is None and remove_label is None:
            results["status"] = "info"
            results["message"] = "没有提供需要更新的字段。"
            if not self.is_agent_mode(locals()):
                console.print("[yellow]提示:[/yellow] 没有提供需要更新的字段。")
            return results

        try:
            session_factory = get_session_factory()
            with session_factory() as session:
                task_repo = TaskRepository(session)

                # --- 处理标签更新 ---
                current_labels = None
                if label is not None or add_label or remove_label:
                    task_to_update = task_repo.get_by_id(task_id)
                    if not task_to_update:
                        results["status"] = "error"
                        results["code"] = 404
                        results["message"] = f"更新失败：未找到 Task ID: {task_id}"
                        if not self.is_agent_mode(locals()):
                            console.print(f"[bold red]错误:[/bold red] 未找到 Task ID: {task_id}")
                        return results
                    current_labels = set(task_to_update.labels or [])

                if label is not None:
                    # 直接设置新标签，覆盖旧的
                    update_data["labels"] = list(set(label))  # 去重
                elif add_label or remove_label:
                    # 添加或移除标签
                    if current_labels is None:
                        current_labels = set()  # Should not happen due to check above, but safeguard
                    if add_label:
                        current_labels.update(add_label)
                    if remove_label:
                        current_labels.difference_update(remove_label)
                    update_data["labels"] = sorted(list(current_labels))

                # 执行更新
                updated_task = task_repo.update_task(task_id, update_data)

                if not updated_task:
                    # update_task 内部可能返回 None 如果 task_id 不存在 (虽然上面检查过一次)
                    results["status"] = "error"
                    results["code"] = 404
                    results["message"] = f"更新失败：未找到 Task ID: {task_id} (或更新时出错)"
                    if not self.is_agent_mode(locals()):
                        console.print(f"[bold red]错误:[/bold red] 更新失败，未找到 Task ID: {task_id}")
                    return results

                session.commit()  # 提交更改

                task_dict = updated_task.to_dict()
                results["data"] = task_dict
                results["message"] = f"成功更新任务 (ID: {updated_task.id})"

                # --- 控制台输出 (非 Agent 模式) ---
                if not self.is_agent_mode(locals()):
                    console.print(f"[bold green]成功:[/bold green] 已更新任务 (ID: {updated_task.id})")
                    # 可以显示更新后的关键信息
                    # console.print(f"  新标题: {updated_task.title}")
                    # console.print(f"  新状态: {updated_task.status}")

        except ValueError as ve:
            logger.error(f"更新任务失败: {ve}", exc_info=True)
            results["message"] = f"更新任务失败: {ve}"
            console.print(f"[bold red]错误:[/bold red] {ve}")
        except Exception as e:
            logger.error(f"更新任务时出错: {e}", exc_info=True)
            # if 'session' in locals() and session.is_active:
            #    session.rollback()
            results["status"] = "error"
            results["code"] = 500
            results["message"] = f"更新任务时出错: {e}"
            if not self.is_agent_mode(locals()):
                console.print(f"[bold red]错误:[/bold red] {e}")

        return results

    def is_agent_mode(self, args: Dict[str, Any]) -> bool:
        """检查是否处于 Agent 模式 (简化)"""
        return False
