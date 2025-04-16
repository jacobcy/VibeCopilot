# src/cli/commands/task/core/show.py

import json
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

from src.core.config import get_config
from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository
from src.models.db.task import Task
from src.roadmap.service.roadmap_service import RoadmapService
from src.services.task import TaskService
from src.utils.file_utils import ensure_directory_exists

logger = logging.getLogger(__name__)
console = Console()


# 获取项目根目录
def get_project_root():
    """获取项目根目录的路径"""
    config = get_config()
    project_root = config.get("paths.project_root", str(Path.cwd()))
    return project_root


# 获取相对于项目根目录的路径
def get_relative_path(path):
    """获取相对于项目根目录的路径"""
    if not path:
        return "未知路径"
    project_root = get_project_root()
    return os.path.relpath(path, project_root)


@click.command(name="show", help="显示任务详情")
@click.argument("task_id", required=False)
@click.option("--verbose", "-v", is_flag=True, help="显示更详细的信息，包括评论")
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml", help="输出格式")
@click.option("--log", is_flag=True, help="显示任务日志")
@click.option("--ref", is_flag=True, help="显示参考资料")
def show_task(task_id: Optional[str] = None, verbose: bool = False, format: str = "yaml", log: bool = False, ref: bool = False) -> None:
    """显示指定任务的详细信息，包括基本信息、描述、关联信息等。

    如果不指定任务ID，则显示当前任务的详情。
    使用 --verbose 选项可以同时显示任务的评论历史。
    使用 --log 选项可以显示任务日志。
    使用 --ref 选项可以显示任务关联的参考资料。
    """
    try:
        # 执行显示任务详情的逻辑
        result = execute_show_task(task_id=task_id, verbose=verbose, format=format, show_log=log, show_ref=ref)

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
    show_log: bool = False,
    show_ref: bool = False,
) -> Dict[str, Any]:
    """执行显示任务详情的核心逻辑

    如果task_id为None，则显示当前任务的详情
    """
    if task_id:
        logger.info(f"执行显示任务命令: task_id={task_id}, verbose={verbose}, show_log={show_log}, show_ref={show_ref}")
    else:
        logger.info(f"执行显示当前任务命令: verbose={verbose}, show_log={show_log}, show_ref={show_ref}")

    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None,
        "meta": {"command": "task show", "args": {"task_id": task_id, "verbose": verbose, "show_log": show_log, "show_ref": show_ref}},
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

            # 如果请求显示日志
            if show_log:
                log_path = os.path.join(".ai", "tasks", task_id, "task.log")
                log_dir = os.path.join(".ai", "tasks", task_id)
                if os.path.exists(log_path):
                    with open(log_path, "r") as f:
                        log_content = f.read()

                    # 简化输出，使用YAML格式
                    log_info = {"任务ID": task_id, "任务标题": task.title, "日志目录": get_relative_path(os.path.abspath(log_dir)), "日志内容": log_content}

                    console.print(yaml.dump(log_info, allow_unicode=True, sort_keys=False))
                else:
                    console.print("\n[bold yellow]未找到任务日志[/bold yellow]")
                    console.print(f"预期路径: {get_relative_path(os.path.abspath(log_path))}")

                # 返回空结果，因为我们已经直接输出了日志内容
                return results

            # 如果请求显示参考资料
            if show_ref:
                # 从数据库中获取Memory引用
                memory_refs = task_repo.get_memory_references(task_id)

                if memory_refs:
                    from src.memory import EntityManager

                    entity_manager = EntityManager()

                    # 准备YAML格式的输出
                    ref_info = {"任务ID": task_id, "任务标题": task.title, "参考资料": []}

                    # 获取并整理每个引用的详细信息
                    for ref in memory_refs:
                        permalink = ref.get("permalink")
                        title = ref.get("title")
                        added_at = ref.get("added_at", "未记录时间")

                        try:
                            # 异步获取实体信息
                            import asyncio

                            entity = asyncio.run(entity_manager.get_entity(permalink))

                            if entity:
                                source_path = entity["properties"].get("file_path", "未知路径")
                                ref_info["参考资料"].append(
                                    {"标题": title, "相对路径": get_relative_path(os.path.abspath(source_path)), "添加时间": added_at, "Memory链接": permalink}
                                )
                            else:
                                ref_info["参考资料"].append({"标题": title, "状态": "不可访问"})
                        except Exception as e:
                            logger.error(f"获取Memory实体时出错: {e}")
                            ref_info["参考资料"].append({"标题": title, "状态": f"获取详情失败: {e}"})
                else:
                    # 如果没有从数据库中找到引用，回退到从日志中查找
                    log_path = os.path.join(".ai", "tasks", task_id, "task.log")
                    ref_info = {"任务ID": task_id, "任务标题": task.title, "参考资料": []}

                    if os.path.exists(log_path):
                        with open(log_path, "r") as f:
                            log_content = f.read()

                        # 查找包含参考文档信息的行
                        import re

                        for line in log_content.splitlines():
                            if "参考文档" in line or "文档路径" in line:
                                match = re.search(r"[参考文档|文档路径]:\s*(.*)", line)
                                if match:
                                    ref_path = match.group(1).strip()
                                    ref_info["参考资料"].append({"标题": os.path.basename(ref_path), "相对路径": get_relative_path(os.path.abspath(ref_path))})

                        if not ref_info["参考资料"]:
                            ref_info["状态"] = "未找到参考资料"
                    else:
                        ref_info["状态"] = "未找到任务日志，无法获取参考资料"
                        ref_info["预期路径"] = get_relative_path(os.path.abspath(log_path))

                # 输出YAML格式
                console.print(yaml.dump(ref_info, allow_unicode=True, sort_keys=False))

                # 返回空结果，因为我们已经直接输出了参考资料
                return results

            task_dict = task.to_dict()
            # 将关联的对象 ID 加入字典，方便 agent 使用
            # 使用 getattr 安全地获取属性，如果不存在则返回 None
            task_dict["roadmap_item_id"] = getattr(task, "roadmap_item_id", None) or task.story_id
            task_dict["workflow_session_id"] = getattr(task, "workflow_session_id", None) or getattr(task, "current_session_id", None)
            task_dict["workflow_stage_instance_id"] = getattr(task, "workflow_stage_instance_id", None)
            task_dict["comments"] = [comment.to_dict() for comment in getattr(task, "comments", [])]

            # 检查是否存在任务日志，添加标志
            log_path = os.path.join(".ai", "tasks", task_id, "task.log")
            task_dict["has_log"] = os.path.exists(log_path)
            task_dict["log_path"] = get_relative_path(os.path.abspath(log_path)) if os.path.exists(log_path) else None

            results["data"] = task_dict
            results["message"] = f"成功检索到任务 {task_id}"

            # --- 控制台输出 ---
            # 基本信息表格
            table = Table(title=f"任务详情: {task.title} (ID: {task.id[:8]})", show_header=False, box=None)
            table.add_column("Field", style="bold blue")
            table.add_column("Value")

            table.add_row("ID", task.id)
            table.add_row("状态", task.status)

            # 获取配置和负责人信息
            config = get_config()
            github_owner = config.get("github.owner", None)

            # 显示负责人信息
            assignee = task.assignee
            if not assignee or assignee == "-":
                # 如果负责人为空或为"-"，则显示默认值
                assignee = "AI Agent"

            # 获取当前负责人
            owner = github_owner if github_owner else "未设置"

            table.add_row("负责人", owner)
            table.add_row("指派给", assignee)

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

            # 添加关联信息
            if getattr(task, "story_id", None):
                table.add_row("关联 Story", task.story_id)

            # 添加当前任务信息
            table.add_row("当前任务", "是" if getattr(task, "is_current", False) else "否")

            # 添加日志和参考资料信息
            log_path = os.path.join(".ai", "tasks", task_id, "task.log")
            log_dir = os.path.join(".ai", "tasks", task_id)
            if os.path.exists(log_path):
                table.add_row("任务日志", f"可用 (使用 --log 查看)")
                table.add_row("日志目录", get_relative_path(os.path.abspath(log_dir)))
            else:
                table.add_row("任务日志", "不可用")

            # 检查参考资料
            memory_refs = task_repo.get_memory_references(task_id)
            if memory_refs:
                ref_count = len(memory_refs)
                table.add_row("参考资料", f"{ref_count} 个可用 (使用 --ref 查看)")

                # 尝试获取第一个参考资料的路径
                try:
                    from src.memory import EntityManager

                    entity_manager = EntityManager()

                    # 只获取第一个引用的路径
                    permalink = memory_refs[0].get("permalink")
                    import asyncio

                    entity = asyncio.run(entity_manager.get_entity(permalink))
                    if entity:
                        source_path = entity["properties"].get("file_path", "未知路径")
                        table.add_row("参考资料路径", get_relative_path(os.path.abspath(source_path)))
                except Exception as e:
                    logger.debug(f"获取参考资料路径时出错: {e}")
            else:
                # 从日志中检查是否有参考资料
                if os.path.exists(log_path):
                    with open(log_path, "r") as f:
                        log_content = f.read()

                    import re

                    ref_docs = []
                    for line in log_content.splitlines():
                        if "参考文档" in line or "文档路径" in line:
                            match = re.search(r"[参考文档|文档路径]:\s*(.*)", line)
                            if match:
                                ref_path = match.group(1).strip()
                                ref_docs.append(ref_path)

                    if ref_docs:
                        table.add_row("参考资料", f"{len(ref_docs)} 个可用 (使用 --ref 查看)")
                        # 显示第一个参考资料的路径
                        table.add_row("参考资料路径", get_relative_path(os.path.abspath(ref_docs[0])))
                    else:
                        table.add_row("参考资料", "无")
                else:
                    table.add_row("参考资料", "无")

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


def _get_task_dir_path(task_id: str) -> Optional[str]:
    """获取任务目录的路径"""
    if not task_id:
        return None
    config = get_config()
    project_root = config.get("paths.project_root", os.getcwd())
    agent_work_dir = config.get("paths.agent_work_dir", ".ai")  # 从配置获取
    task_dir = os.path.join(project_root, agent_work_dir, "tasks", task_id)
    return task_dir


def _get_task_log_path(task_id: str) -> Optional[str]:
    """获取任务日志文件的路径"""
    task_dir = _get_task_dir_path(task_id)
    if not task_dir:
        return None
    log_path = os.path.join(task_dir, "task.log")
    # 确保目录存在（虽然 get_task_dir_path 应该做了，但再次确认无妨）
    ensure_directory_exists(os.path.dirname(log_path))
    return log_path


def _read_task_log(task_id: str, last_n: Optional[int] = None) -> Optional[str]:
    """读取任务日志内容"""
    log_path = _get_task_log_path(task_id)
    if not log_path or not os.path.exists(log_path):
        return "任务日志文件不存在。"
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if last_n is not None and last_n > 0:
                return "".join(lines[-last_n:])
            else:
                return "".join(lines)
    except Exception as e:
        return f"读取任务日志失败: {e}"


def _get_task_metadata(task_id: str) -> Optional[Dict[str, Any]]:
    """获取任务元数据"""
    task_dir = _get_task_dir_path(task_id)
    if not task_dir:
        return None
    metadata_path = os.path.join(task_dir, "metadata.json")
    if not os.path.exists(metadata_path):
        return None
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _format_task_details(task: Task, metadata: Optional[Dict[str, Any]] = None) -> Panel:
    """格式化任务详情以便显示"""
    # ... (省略格式化逻辑)


def _format_task_summary(task: Task) -> str:
    """格式化任务摘要"""
    # ... (省略格式化逻辑)


def show_task_details(
    task_service: TaskService,
    roadmap_service: Optional[RoadmapService],
    task_id: str,
    show_log: bool = False,
    log_lines: Optional[int] = None,
    verbose: bool = False,
) -> bool:
    """显示任务详情的核心逻辑"""
    # ... (省略获取任务、元数据、工作流等逻辑)

    # 显示日志
    if show_log:
        log_content = _read_task_log(task_id, last_n=log_lines)
        # ... (省略日志显示逻辑)

    return True
