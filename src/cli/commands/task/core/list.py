# src/cli/commands/task/core/list.py

import logging
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table

from src.db import get_session_factory
from src.db.repositories import TaskRepository

console = Console()
logger = logging.getLogger(__name__)


@click.command(name="list", help="列出项目中的任务")
@click.option("--status", "-s", multiple=True, help="按状态过滤 (例如: open,in_progress)")
@click.option("--assignee", "-a", help="按负责人过滤")
@click.option("--label", "-l", multiple=True, help="按标签过滤 (目前仅简单匹配)")
@click.option("--roadmap", "-r", help="按关联的 Story ID 过滤")
@click.option("--independent", "-i", is_flag=True, help="仅显示独立任务 (无 Story 关联)")
@click.option("--temp", "-t", type=click.Choice(["yes", "no", "all"]), default="all", help="过滤临时任务 (yes: 仅显示临时任务, no: 仅显示有 Story 关联的任务, all: 显示所有任务)")
@click.option("--limit", type=int, help="限制返回数量")
@click.option("--offset", type=int, help="跳过指定数量的结果")
@click.option("--verbose", "-v", is_flag=True, help="显示更详细的信息")
@click.option("--format", type=click.Choice(["yaml", "json"]), default="yaml", help="输出格式")
def list_tasks(
    status: List[str],
    assignee: Optional[str],
    label: List[str],
    roadmap: Optional[str],
    independent: bool,
    temp: str,
    limit: Optional[int],
    offset: Optional[int],
    verbose: bool,
    format: str,
) -> None:
    """列出项目中的任务

    用于列出和过滤项目中的任务。支持按状态、负责人、标签等条件过滤，
    并可以通过 --verbose 选项显示更详细的任务信息。
    """
    try:
        # 执行列出任务的逻辑
        result = execute_list_tasks(
            status=list(status) if status else None,
            assignee=assignee,
            label=list(label) if label else None,
            roadmap_item_id=roadmap,
            independent=independent,
            temp=temp,  # 添加临时任务过滤参数
            limit=limit,
            offset=offset,
            verbose=verbose,
            format=format,
        )

        # 处理执行结果
        if result["status"] == "success":
            if not result.get("data"):
                console.print("[yellow]未找到符合条件的任务。[/yellow]")
                return 0

            # 格式化输出 - 使用task_click模块的format_output
            if format.lower() == "json":
                import json

                print(json.dumps(result["data"], ensure_ascii=False, indent=2))
            else:  # 默认使用YAML
                import yaml

                print(yaml.safe_dump(result["data"], allow_unicode=True, sort_keys=False))
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"列出任务时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


def execute_list_tasks(
    status: Optional[List[str]] = None,
    assignee: Optional[str] = None,
    label: Optional[List[str]] = None,
    roadmap_item_id: Optional[str] = None,
    independent: Optional[bool] = None,
    temp: Optional[str] = "all",  # "yes", "no", "all"
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    verbose: bool = False,
    format: str = "yaml",
) -> Dict[str, Any]:
    """执行列出任务的核心逻辑"""
    logger.info(
        f"执行任务列表命令: status={status}, assignee={assignee}, label={label}, "
        f"roadmap_item_id={roadmap_item_id}, independent={independent}, temp={temp}, "
        f"limit={limit}, offset={offset}, verbose={verbose}, format={format}"
    )

    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": [],
        "meta": {"command": "task list", "args": locals()},
    }

    # 处理独立任务过滤参数
    is_independent_filter = None
    if independent is True:
        is_independent_filter = True
    elif independent is False:
        is_independent_filter = False

    # 处理临时任务过滤参数
    is_temporary_filter = None
    if temp == "yes":
        is_temporary_filter = True
    elif temp == "no":
        is_temporary_filter = False
    # "all" 不设置过滤条件

    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            task_repo = TaskRepository(session)
            tasks = task_repo.search_tasks(
                status=status,
                assignee=assignee,
                labels=label,
                roadmap_item_id=roadmap_item_id,
                is_independent=is_independent_filter,
                is_temporary=is_temporary_filter,  # 添加临时任务过滤参数
                limit=limit,
                offset=offset,
            )

            task_dicts = [task.to_dict() for task in tasks]
            results["data"] = task_dicts
            results["message"] = f"成功检索到 {len(task_dicts)} 个任务"

            # --- 控制台输出 ---
            if not tasks:
                console.print("[yellow]未找到符合条件的任务。[/yellow]")
                return results

            table = Table(title="任务列表")
            table.add_column("ID", style="dim", width=12)
            table.add_column("标题", style="bold cyan")
            table.add_column("状态", style="magenta")
            table.add_column("负责人", style="green")
            if verbose:
                table.add_column("类型", style="dim")
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
                    # 添加任务类型：临时任务或正式任务
                    task_type = "临时任务" if task.story_id is None else "正式任务"
                    row.append(task_type)
                    # 关联Story
                    row.append(task.story_id if task.story_id else "-")
                    # 创建时间
                    created_time = "-"
                    if hasattr(task, "created_at") and task.created_at:
                        if hasattr(task.created_at, "strftime"):
                            created_time = task.created_at.strftime("%Y-%m-%d %H:%M")
                        else:
                            created_time = str(task.created_at)
                    row.append(created_time)
                table.add_row(*row)

            console.print(table)

    except Exception as e:
        logger.error(f"列出任务时出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"列出任务时出错: {e}"
        console.print(f"[bold red]错误:[/bold red] {e}")

    return results
