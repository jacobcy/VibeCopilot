"""
关联任务命令模块
"""

import logging
import re
from enum import Enum
from typing import Any, Dict, Optional, Tuple

import click
from rich.console import Console

from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository
from src.models.db.task import Task

logger = logging.getLogger(__name__)
console = Console()


class LinkType(str, Enum):
    """支持的链接类型枚举"""

    ROADMAP = "roadmap"
    WORKFLOW_STAGE = "workflow_stage"
    GITHUB_ISSUE = "github_issue"
    GITHUB_PR = "github_pr"
    GITHUB_COMMIT = "github_commit"


def _parse_github_ref(ref: str, delimiter: str) -> Tuple[str, str]:
    """解析 GitHub 引用 (e.g., owner/repo#123 or owner/repo@sha)"""
    if delimiter not in ref or "/" not in ref.split(delimiter)[0]:
        raise ValueError(f"GitHub 引用格式应为 'owner/repo{delimiter}identifier'")
    repo_part, identifier = ref.split(delimiter, 1)
    if not repo_part or not identifier:
        raise ValueError(f"GitHub 引用格式应为 'owner/repo{delimiter}identifier'")
    return repo_part, identifier


def is_agent_mode() -> bool:
    """检查是否处于 Agent 模式"""
    return False


def execute_link_task(
    task_id: str,
    link_type: LinkType,
    target_id: str,
) -> Dict[str, Any]:
    """执行关联任务的逻辑"""
    logger.info(f"执行关联任务命令: task_id={task_id}, type={link_type}, target={target_id}")

    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None,
        "meta": {
            "command": "task link",
            "args": {"task_id": task_id, "link_type": link_type.value, "target_id": target_id},
        },
    }

    unlink = target_id == "-"
    target_value = None if unlink else target_id

    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            task_repo = TaskRepository(session)
            updated_task: Optional[Task] = None

            if link_type == LinkType.ROADMAP:
                updated_task = task_repo.link_to_roadmap(task_id, target_value)
                link_desc = f"Roadmap Item (Story ID: {target_value})" if not unlink else "Roadmap Item"

            elif link_type == LinkType.WORKFLOW_STAGE:
                updated_task = task_repo.link_to_workflow_stage(task_id, target_value)
                link_desc = f"Workflow Stage Instance (ID: {target_value})" if not unlink else "Workflow Stage Instance"

            elif link_type == LinkType.GITHUB_ISSUE:
                issue_number = None
                if not unlink:
                    repo_part, issue_num_str = _parse_github_ref(target_value, "#")
                    issue_number = int(issue_num_str)
                updated_task = task_repo.link_to_github_issue(task_id, issue_number)
                link_desc = f"GitHub Issue ({target_value})" if not unlink else "GitHub Issue"

            elif link_type == LinkType.GITHUB_PR:
                if unlink:
                    repo_part, pr_num_str = _parse_github_ref(target_value, "#")
                    pr_number = int(pr_num_str)
                    updated_task = task_repo.remove_linked_pr(task_id, repo_part, pr_number)
                    link_desc = f"GitHub PR ({target_value})"
                else:
                    repo_part, pr_num_str = _parse_github_ref(target_value, "#")
                    pr_number = int(pr_num_str)
                    updated_task = task_repo.add_linked_pr(task_id, repo_part, pr_number)
                    link_desc = f"GitHub PR ({target_value})"

            elif link_type == LinkType.GITHUB_COMMIT:
                if unlink:
                    repo_part, sha = _parse_github_ref(target_value, "@")
                    updated_task = task_repo.remove_linked_commit(task_id, repo_part, sha)
                    link_desc = f"GitHub Commit ({target_value})"
                else:
                    repo_part, sha = _parse_github_ref(target_value, "@")
                    updated_task = task_repo.add_linked_commit(task_id, repo_part, sha)
                    link_desc = f"GitHub Commit ({target_value})"
            else:
                raise ValueError(f"不支持的链接类型: {link_type}")

            if not updated_task:
                results["status"] = "error"
                results["code"] = 404
                results["message"] = f"操作失败：未找到 Task ID: {task_id} 或关联操作内部出错。"
                if not is_agent_mode():
                    console.print(f"[bold red]错误:[/bold red] 未找到 Task ID: {task_id} 或关联操作失败。")
                return results

            session.commit()

            results["data"] = updated_task.to_dict()
            action = "取消关联" if unlink else "关联"
            results["message"] = f"成功将任务 {task_id} {action}到 {link_desc}"

            if not is_agent_mode():
                console.print(f"[bold green]成功:[/bold green] 已将任务 {task_id} {action}到 {link_desc}")

    except ValueError as ve:
        logger.warning(f"解析目标链接失败: {ve}")
        results["status"] = "error"
        results["code"] = 400
        results["message"] = f"无效的目标格式: {ve}"
        console.print(f"[bold red]错误:[/bold red] 无效的目标格式: {ve}")
        return results

    except Exception as e:
        logger.error(f"关联任务时出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"关联任务时出错: {e}"
        if not is_agent_mode():
            console.print(f"[bold red]错误:[/bold red] {e}")

    return results


@click.command(help="关联任务到 Roadmap Item, Workflow Stage 或 GitHub 实体")
@click.argument("task_id", type=str)
@click.option(
    "-t",
    "--type",
    "link_type",
    type=click.Choice([t.value for t in LinkType]),
    required=True,
    help="关联类型 (roadmap, workflow_stage, github_issue, github_pr, github_commit)",
)
@click.option("--target", "target_id", type=str, required=True, help="目标实体ID。使用'-'来取消关联。对于GitHub实体，格式为'owner/repo#123'或'owner/repo@sha'")
def link_task(task_id: str, link_type: str, target_id: str):
    """关联任务到其他实体命令

    将任务关联到其他实体，如Roadmap Item、Workflow Stage或GitHub实体。
    支持添加和移除关联关系。对于GitHub实体，支持关联到Issue、PR和Commit。

    示例:
        vibecopilot task link abc123 -t roadmap --target S1
        vibecopilot task link def456 -t github_issue --target owner/repo#123
        vibecopilot task link ghi789 -t github_pr --target owner/repo#456
        vibecopilot task link jkl012 -t github_commit --target owner/repo@abcdef123
        vibecopilot task link mno345 -t roadmap --target - # 取消关联
    """
    try:
        # 转换字符串类型到枚举类型
        link_type_enum = LinkType(link_type)

        # 执行关联任务逻辑
        result = execute_link_task(task_id, link_type_enum, target_id)

        # 命令行执行时不需要返回值
        return result
    except Exception as e:
        logger.error(f"执行关联任务命令时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return {"status": "error", "message": str(e)}
