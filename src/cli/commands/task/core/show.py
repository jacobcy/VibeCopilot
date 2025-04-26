# src/cli/commands/task/core/show.py

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.cli.commands.task.utils.format import format_task_output
from src.cli.commands.task.utils.show_log import show_task_log
from src.cli.commands.task.utils.show_ref import show_task_references
from src.core.config import get_config
from src.db.session_manager import session_scope
from src.services.task.core import TaskService

logger = logging.getLogger(__name__)
console = Console()


def get_relative_path(path: str) -> str:
    """获取相对于项目根目录的路径

    Args:
        path: 文件路径

    Returns:
        相对路径字符串
    """
    if not path:
        return "未知路径"

    config = get_config()
    project_root = config.get("paths.project_root", str(Path.cwd()))
    return os.path.relpath(path, project_root)


@click.command("show")
@click.argument("task_id", required=False)
@click.option("--verbose", "-v", is_flag=True, help="显示详细信息")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "yaml"]),
    default="yaml",
    help="输出格式",
)
@click.option("--log", "-l", is_flag=True, help="显示任务日志")
@click.option("--ref", "-r", is_flag=True, help="显示参考资料")
@click.option("--comments", "-c", is_flag=True, help="显示评论")
def show(task_id: Optional[str], verbose: bool, format: str, log: bool, ref: bool, comments: bool) -> None:
    """显示任务详情

    如果未提供 TASK_ID，则显示当前活动任务。
    可以通过选项控制输出格式、是否显示日志、参考资料和评论。
    """
    try:
        result = execute_show_task(task_id, verbose, format, log, ref, comments)
        if result["code"] != 0:
            raise click.ClickException(result["message"])
    except Exception as e:
        logger.error(f"显示任务失败: {e}", exc_info=True)
        raise click.ClickException(str(e))


def execute_show_task(
    task_id: Optional[str],
    verbose: bool = False,
    format: str = "yaml",
    log: bool = False,
    ref: bool = False,
    comments: bool = False,
) -> Dict[str, Any]:
    """执行任务显示

    Args:
        task_id: 任务ID，如果为None，则尝试获取当前任务
        verbose: 是否显示详细信息
        format: 输出格式(json/yaml)
        log: 是否显示任务日志
        ref: 是否显示参考资料
        comments: 是否显示评论

    Returns:
        包含操作结果的字典
    """
    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None,
    }

    try:
        task = None
        task_comments = []
        current_task_id = task_id

        # --- Database Operations within session_scope ---
        with session_scope() as session:
            task_service = TaskService()

            # 如果没有提供 task_id，尝试获取当前任务
            if current_task_id is None:
                logger.info("未提供任务ID，尝试获取当前任务...")
                current_task_obj = task_service.get_current_task(session)
                if current_task_obj:
                    current_task_id = current_task_obj.get("id")
                    logger.info(f"找到当前任务: {current_task_id}")
                    console.print(f"[dim]显示当前任务: {current_task_obj.get('title', current_task_id)}[/dim]")
                else:
                    results["status"] = "error"
                    results["code"] = 404
                    results["message"] = "未提供任务ID，且当前没有活动任务。请使用 'vc task update --current <TASK_ID>' 设置或提供一个任务ID。"
                    return results

            # 验证 current_task_id 是否有效 (确保非 None)
            if not current_task_id:
                results["status"] = "error"
                results["code"] = 500  # Internal error, should have been caught earlier
                results["message"] = "内部错误：无法确定要显示的任务ID。"
                return results

            # 获取任务信息
            task = task_service.get_task(session, current_task_id)
            if not task:
                results["status"] = "error"
                results["code"] = 404
                results["message"] = f"任务 {current_task_id} 不存在"
                return results

            # Get comments if requested
            if comments:
                task_comments = task_service.get_task_comments(session, current_task_id)

        # --- Process and display results outside the session ---
        if task:
            # 调用格式化函数
            output_content = format_task_output(task, format, verbose)

            # 根据返回类型打印
            if isinstance(output_content, Table):
                console.print(output_content)
            else:  # 假设是字符串 (JSON/YAML)
                console.print(output_content)

            results["data"] = task

            # Display log if requested
            if log:
                log_result = show_task_log(current_task_id, task.get("title", "未知任务"))
                if log_result["code"] != 0:
                    results["status"] = "warning"
                    results["message"] += f" 显示日志时出错: {log_result['message']}\n"

            # Display references if requested
            if ref:
                memory_link = task.get("memory_link")
                ref_result = show_task_references(current_task_id, task.get("title", "未知任务"), memory_link)
                if ref_result["code"] != 0:
                    results["status"] = "warning"
                    results["message"] += f" 显示参考时出错: {ref_result['message']}\n"

            # Display comments
            if comments:
                if task_comments:
                    console.print("\n[bold underline]评论:[/bold underline]")
                    for comment in task_comments:
                        comment_panel = Panel(
                            Markdown(comment.get("content", "")),
                            title=f"评论者: {comment.get('author', '匿名')} @ {comment.get('created_at', '未知时间')}",
                            border_style="cyan",
                            title_align="left",
                        )
                        console.print(comment_panel)
                else:
                    console.print("\n[dim]无评论[/dim]")

            if results["status"] == "success":
                results["message"] = f"成功显示任务 {current_task_id} 信息"
            elif results["status"] == "warning" and not results["message"]:
                results["message"] = f"成功显示任务 {current_task_id} 信息，但显示附加信息时出现警告。"

    except Exception as e:
        logger.error(f"显示任务数据库操作期间出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"显示任务时出错: {e}"

    return results
