# src/cli/commands/task/core/update.py

"""
更新任务命令模块
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import click
from loguru import logger
from rich.console import Console

# 导入任务日志相关函数和Memory存储函数
from src.cli.commands.task.core.memory import append_to_task_log, store_ref_to_memory
from src.db import get_session_factory
from src.db.repositories.roadmap_repository import RoadmapRepository
from src.db.repositories.stage_repository import StageRepository
from src.db.repositories.task_repository import TaskRepository
from src.models.db.roadmap import Roadmap
from src.models.db.stage import Stage
from src.services.task import TaskService

logger = logging.getLogger(__name__)
console = Console()

# 定义有效的任务状态
VALID_TASK_STATUSES = ["todo", "in_progress", "done", "blocked", "review", "backlog"]


def parse_github_url(url: str) -> Tuple[str, int]:
    """
    解析GitHub URL，提取仓库信息和issue编号

    支持的格式:
    - https://github.com/owner/repo/issues/123
    - owner/repo#123

    Args:
        url: GitHub URL

    Returns:
        Tuple[str, int]: (仓库路径, issue编号)

    Raises:
        ValueError: 当URL格式无效时
    """
    # 尝试解析完整URL格式
    url_pattern = r"https?://github\.com/([^/]+/[^/]+)/issues/(\d+)"
    url_match = re.match(url_pattern, url)

    if url_match:
        repo = url_match.group(1)
        issue_number = int(url_match.group(2))
        return repo, issue_number

    # 尝试解析简短格式
    short_pattern = r"([^/]+/[^#]+)#(\d+)"
    short_match = re.match(short_pattern, url)

    if short_match:
        repo = short_match.group(1)
        issue_number = int(short_match.group(2))
        return repo, issue_number

    raise ValueError(f"无效的GitHub URL格式: {url}。支持的格式: 'owner/repo#123' 或 'https://github.com/owner/repo/issues/123'")


@click.command(name="update", help="更新现有任务的信息")
@click.argument("task_id")
@click.option("--title", "-t", help="任务标题")
@click.option("--desc", "--description", "-d", help="任务描述")
@click.option("--status", "-s", help="任务状态")
@click.option("--assignee", "-a", help="任务负责人")
@click.option("--labels", "-l", multiple=True, help="任务标签 (可设置多个)")
@click.option("--due", "--due-date", help="截止日期 (格式: YYYY-MM-DD，设置为'clear'可清除截止日期)")
@click.option("--roadmap", "-r", help="关联的路线图项目 ID")
@click.option("--flow", "--workflow", "-w", help="关联的工作流阶段 ID")
@click.option("--github", "-g", help="关联的 GitHub Issue URL")
@click.option("--link-story", "-ls", help="关联的故事 ID")
@click.option("--unlink", "-ul", help="取消关联的故事或 GitHub Issue")
@click.option("--ref", "--reference", help="关联参考文档路径")
def update_task(
    task_id: str,
    title: Optional[str] = None,
    desc: Optional[str] = None,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    due: Optional[str] = None,
    roadmap: Optional[str] = None,
    flow: Optional[str] = None,
    github: Optional[str] = None,
    link_story: Optional[str] = None,
    unlink: Optional[str] = None,
    ref: Optional[str] = None,
) -> int:
    """
    更新现有任务的信息。

    提供需要更新的字段，未提供的字段将保持不变。

    参数:
        task_id: 要更新的任务ID
        title: 新的任务标题
        desc: 新的任务描述
        status: 新的任务状态
        assignee: 新的任务负责人
        labels: 新的任务标签列表
        due: 新的截止日期
        roadmap: 新关联的路线图项目ID
        flow: 新关联的工作流阶段ID
        github: 新关联的GitHub Issue URL
        link_story: 新关联的故事 ID
        unlink: 取消关联的故事或 GitHub Issue
        ref: 关联的参考文档路径
    """
    try:
        # 检查是否提供了至少一个更新参数
        if not any([title, desc, status, assignee, labels, due, roadmap, flow, github, link_story, unlink, ref]):
            console.print("[bold yellow]警告:[/bold yellow] 未提供任何需要更新的字段。使用 --help 查看可用选项。")
            return 1

        # 调用执行逻辑
        result = execute_update_task(
            task_id=task_id,
            title=title,
            description=desc,
            status=status,
            assignee=assignee,
            labels=labels,
            due_date=due,
            roadmap_id=roadmap,
            workflow_id=flow,
            github_url=github,
            link_story=link_story,
            unlink=unlink,
            ref_path=ref,
        )

        # 处理执行结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"更新任务时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


def execute_update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None,
    due_date: Optional[str] = None,
    roadmap_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    github_url: Optional[str] = None,
    link_story: Optional[str] = None,
    unlink: Optional[str] = None,
    ref_path: Optional[str] = None,
) -> Dict[str, Any]:
    """执行更新任务的核心逻辑"""
    logger.info(f"执行更新任务命令: task_id={task_id}")

    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None,
        "meta": {
            "command": "task update",
            "args": {
                "task_id": task_id,
                "title": title,
                "description": description,
                "status": status,
                "assignee": assignee,
                "labels": labels,
                "due_date": due_date,
                "roadmap_id": roadmap_id,
                "workflow_id": workflow_id,
                "github_url": github_url,
                "link_story": link_story,
                "unlink": unlink,
                "ref_path": ref_path,
            },
        },
    }

    # 记录任务更新
    log_updates = {}

    if title:
        log_updates["标题"] = title
    if description:
        log_updates["描述"] = description
    if status:
        log_updates["状态"] = status
    if assignee:
        log_updates["负责人"] = assignee
    if labels:
        log_updates["标签"] = ", ".join(labels)
    if due_date:
        log_updates["截止日期"] = due_date
    if ref_path:
        log_updates["参考文档"] = ref_path

    # 解析GitHub链接
    github_repo = None
    github_issue_number = None
    if github_url:
        try:
            github_repo, github_issue_number = parse_github_url(github_url)
            log_updates["GitHub Issue"] = f"{github_repo}#{github_issue_number}"
        except ValueError as e:
            results["status"] = "error"
            results["code"] = 400
            results["message"] = f"GitHub URL 格式无效: {e}"
            return results

    # 验证任务状态值
    if status and status not in VALID_TASK_STATUSES:
        valid_statuses = ", ".join(VALID_TASK_STATUSES)
        results["status"] = "error"
        results["code"] = 400
        results["message"] = f"无效的任务状态: {status}。有效状态值为: {valid_statuses}"
        return results

    session_factory = get_session_factory()
    with session_factory() as session:
        try:
            task_repo = TaskRepository(session)

            # 检查任务是否存在
            task = task_repo.get_by_id(task_id)
            if not task:
                results["status"] = "error"
                results["code"] = 404
                results["message"] = f"更新失败: 未找到任务 {task_id}"
                return results

            # 验证路线图存在
            if roadmap_id:
                roadmap_repo = RoadmapRepository(session)
                roadmap_item = roadmap_repo.get_by_id(roadmap_id)
                if not roadmap_item:
                    results["status"] = "error"
                    results["code"] = 404
                    results["message"] = f"更新失败: 未找到路线图项目 {roadmap_id}"
                    return results
                log_updates["路线图项目"] = roadmap_id

            # 验证工作流阶段存在
            if workflow_id:
                stage_repo = StageRepository(session)
                workflow_stage = stage_repo.get_by_id(workflow_id)
                if not workflow_stage:
                    results["status"] = "error"
                    results["code"] = 404
                    results["message"] = f"更新失败: 未找到工作流阶段 {workflow_id}"
                    return results
                log_updates["工作流阶段"] = workflow_id

            # 记录日志 - 只有在有字段更新时才记录
            if log_updates:
                append_to_task_log(task_id, "任务更新", log_updates)

            # 如果提供了参考文档路径，存储到Memory并关联
            if ref_path:
                try:
                    memory_result = store_ref_to_memory(task_id, ref_path)
                    if not memory_result["success"]:
                        logger.warning(f"存储参考文档到Memory失败: {memory_result.get('error')}")
                        console.print(f"[bold yellow]警告:[/bold yellow] 存储参考文档到Memory失败: {memory_result.get('error')}")
                    elif memory_result.get("updated", False):
                        logger.info(f"更新参考文档到Memory成功: {memory_result.get('permalink')}")
                        console.print(f"[bold green]成功:[/bold green] 更新参考文档到Memory")
                    else:
                        # 检查是否为模拟数据
                        if memory_result.get("simulated", False):
                            logger.warning(f"生成模拟参考链接: {memory_result.get('permalink')}")
                            console.print(f"[bold yellow]注意:[/bold yellow] 生成模拟参考链接 {memory_result.get('permalink')}")
                            console.print("[bold yellow]      [/bold yellow] 文档未实际存储到Memory，只创建了引用记录")
                            console.print("[bold yellow]建议:[/bold yellow] 在Cursor IDE环境中执行此操作以实际存储文档")
                        else:
                            logger.info(f"存储参考文档到Memory成功: {memory_result.get('permalink')}")
                            console.print(f"[bold green]成功:[/bold green] 存储参考文档到Memory")
                except Exception as e:
                    logger.error(f"存储参考文档到Memory时出错: {e}")
                    console.print(f"[bold yellow]警告:[/bold yellow] 存储参考文档到Memory时出错: {e}")

            # 准备更新数据
            update_data = {}
            if title is not None:
                update_data["title"] = title
            if description is not None:
                update_data["description"] = description
            if status is not None:
                update_data["status"] = status  # 直接使用字符串状态
            if assignee is not None:
                update_data["assignee"] = assignee
            if labels is not None:
                update_data["labels"] = labels
            if due_date is not None:
                if due_date.lower() == "clear":
                    update_data["due_date"] = None  # 设置为None以清除截止日期
                else:
                    update_data["due_date"] = due_date
            if roadmap_id is not None:
                update_data["roadmap_id"] = roadmap_id
            if workflow_id is not None:
                update_data["workflow_stage_id"] = workflow_id
            if github_url is not None:
                update_data["github_repo"] = github_repo
                update_data["github_issue_number"] = github_issue_number
            if link_story:
                update_data["story_id"] = link_story
            if unlink:
                if unlink == "story":
                    update_data["story_id"] = None
                elif unlink == "github":
                    update_data["github_issue"] = None

            # 执行更新
            success = task_repo.update(task_id, update_data)
            if success:
                session.commit()
                updated_fields = ", ".join(update_data.keys())
                results["message"] = f"成功更新任务 {task_id} (更新字段: {updated_fields})"
                results["data"] = {"task_id": task_id, "updated": True, "updated_fields": list(update_data.keys())}
            else:
                session.rollback()
                results["status"] = "error"
                results["code"] = 500
                results["message"] = f"更新任务 {task_id} 失败"

        except Exception as e:
            session.rollback()
            logger.error(f"更新任务时出错: {e}", exc_info=True)
            results["status"] = "error"
            results["code"] = 500
            results["message"] = f"更新任务时出错: {e}"

    return results
