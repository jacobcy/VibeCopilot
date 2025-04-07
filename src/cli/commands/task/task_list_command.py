# src/cli/commands/task/task_list_command.py

import logging
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.table import Table

from src.cli.commands.base_command import BaseCommand
from src.db import get_session_factory
from src.db.repositories import TaskRepository
from src.db.service import DatabaseService

logger = logging.getLogger(__name__)
console = Console()


class ListTaskCommand(BaseCommand):
    """列出任务命令

    用于列出和过滤项目中的任务。支持按状态、负责人、标签等条件过滤，
    并可以通过 --verbose 选项显示更详细的任务信息。

    选项:
        --status, -s: 按状态过滤 (例如: open,in_progress)
        --assignee, -a: 按负责人过滤
        --label, -l: 按标签过滤
        --roadmap, -r: 按关联的 Story ID 过滤
        --independent, -i: 仅显示独立任务
        --limit: 限制返回数量
        --offset: 跳过指定数量的结果
        --verbose, -v: 显示更详细的信息
    """

    def __init__(self):
        super().__init__("list", "列出项目中的任务")

    def execute(
        self,
        status: Optional[List[str]] = typer.Option(None, "--status", "-s", help="按状态过滤 (例如: open,in_progress)"),
        assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="按负责人过滤"),
        label: Optional[List[str]] = typer.Option(None, "--label", "-l", help="按标签过滤 (目前仅简单匹配)"),
        roadmap_item_id: Optional[str] = typer.Option(None, "--roadmap", "-r", help="按关联的 Roadmap Item (Story ID) 过滤"),
        independent: Optional[bool] = typer.Option(None, "--independent", "-i", help="仅显示独立任务 (无 Roadmap 关联)"),
        limit: Optional[int] = typer.Option(None, "--limit", help="限制返回数量"),
        offset: Optional[int] = typer.Option(None, "--offset", help="跳过指定数量的结果"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="显示更详细的信息"),
    ) -> Dict[str, Any]:
        """执行列出任务的逻辑"""
        logger.info(
            f"执行任务列表命令: status={status}, assignee={assignee}, label={label}, "
            f"roadmap_item_id={roadmap_item_id}, independent={independent}, limit={limit}, offset={offset}, verbose={verbose}"
        )

        results = {
            "status": "success",
            "code": 0,
            "message": "",
            "data": [],
            "meta": {"command": "task list", "args": locals()},
        }

        is_independent_filter = None
        if independent is True:
            is_independent_filter = True
        elif independent is False:
            is_independent_filter = False

        try:
            session_factory = get_session_factory()
            with session_factory() as session:
                task_repo = TaskRepository(session)
                tasks = task_repo.search_tasks(
                    status=status,
                    assignee=assignee,
                    labels=label,  # 注意：Repository 中的 labels 过滤可能需要完善
                    roadmap_item_id=roadmap_item_id,
                    is_independent=is_independent_filter,
                    limit=limit,
                    offset=offset,
                )

                task_dicts = [task.to_dict() for task in tasks]
                results["data"] = task_dicts
                results["message"] = f"成功检索到 {len(task_dicts)} 个任务"

                # --- 控制台输出 (非 Agent 模式) ---
                if not self.is_agent_mode(locals()):  # 假设有方法判断是否 agent mode
                    if not tasks:
                        console.print("[yellow]未找到符合条件的任务。[/yellow]")
                        return results

                    table = Table(title="任务列表")
                    table.add_column("ID", style="dim", width=12)
                    table.add_column("标题", style="bold cyan")
                    table.add_column("状态", style="magenta")
                    table.add_column("负责人", style="green")
                    if verbose:
                        table.add_column("关联 Story", style="dim")
                        table.add_column("创建时间", style="dim")

                    for task in tasks:
                        row = [
                            task.id[:8] + "..." if not verbose else task.id,
                            task.title,
                            task.status,
                            task.assignee if task.assignee else "-",
                        ]
                        if verbose:
                            row.append(task.roadmap_item_id if task.roadmap_item_id else "-")
                            row.append(task.created_at.strftime("%Y-%m-%d %H:%M") if task.created_at else "-")
                        table.add_row(*row)

                    console.print(table)

        except Exception as e:
            logger.error(f"列出任务时出错: {e}", exc_info=True)
            results["status"] = "error"
            results["code"] = 500
            results["message"] = f"列出任务时出错: {e}"
            if not self.is_agent_mode(locals()):
                console.print(f"[bold red]错误:[/bold red] {e}")

        return results

    def is_agent_mode(self, args: Dict[str, Any]) -> bool:
        """检查是否处于 Agent 模式 (简化)"""
        # 实际实现可能更复杂，例如检查特定环境变量或参数
        return False
