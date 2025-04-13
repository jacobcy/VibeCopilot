# src/cli/commands/task/core/create.py

import logging
from typing import Any, Dict, List, Optional

import click
from rich.console import Console

from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository

console = Console()
logger = logging.getLogger(__name__)


@click.command(name="create", help="创建一个新的任务")
@click.option("-t", "--title", required=True, help="任务标题 (必需)")
@click.option("-d", "--desc", help="任务描述")
@click.option("-a", "--assignee", help="负责人")
@click.option("-l", "--label", multiple=True, help="标签 (可多次使用)")
@click.option("-s", "--status", default="open", help="初始状态 (默认: open)")
@click.option("--link-roadmap", help="关联到 Roadmap Item (Story ID)")
@click.option("--link-workflow-stage", help="关联到 Workflow Stage Instance ID")
@click.option("--link-github", help="关联到 GitHub Issue (格式: owner/repo#number)")
def create_task(title, desc, assignee, label, status, link_roadmap, link_workflow_stage, link_github):
    """创建一个新的任务

    创建一个新的任务，支持设置标题、描述、负责人、标签等基本信息，
    以及关联到 Roadmap Item、Workflow Stage 或 GitHub Issue。
    """
    try:
        # 执行创建任务的逻辑
        result = execute_create_task(
            title=title,
            description=desc,
            assignee=assignee,
            label=list(label) if label else None,
            status=status,
            link_roadmap_item_id=link_roadmap,
            link_workflow_stage_instance_id=link_workflow_stage,
            link_github_issue=link_github,
        )

        # 输出结果
        if result["status"] == "success":
            console.print(f"[bold green]成功:[/bold green] {result['message']}")
            if result.get("data"):
                # 使用task_click模块中的format_output函数格式化输出
                from src.cli.commands.task.task_click import format_output

                print(format_output(result["data"], format="yaml", verbose=True))
            return 0
        else:
            console.print(f"[bold red]错误:[/bold red] {result['message']}")
            return 1

    except Exception as e:
        logger.error(f"创建任务时出错: {e}", exc_info=True)
        console.print(f"[bold red]错误:[/bold red] {e}")
        return 1


def execute_create_task(
    title: str,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    label: Optional[List[str]] = None,
    status: Optional[str] = "open",
    link_roadmap_item_id: Optional[str] = None,
    link_workflow_stage_instance_id: Optional[str] = None,
    link_github_issue: Optional[str] = None,
) -> Dict[str, Any]:
    """执行创建任务的核心逻辑"""
    logger.info(
        f"执行创建任务命令: title='{title}', assignee={assignee}, "
        f"labels={label}, status={status}, "
        f"link_roadmap={link_roadmap_item_id}, "
        f"link_stage={link_workflow_stage_instance_id}, "
        f"link_github={link_github_issue}"
    )

    results = {
        "status": "success",
        "code": 0,
        "message": "",
        "data": None,
        "meta": {
            "command": "task create",
            "args": locals(),
        },
    }

    task_data = {
        "title": title,
        "description": description,
        "assignee": assignee,
        "labels": label,
        "status": status,
        "roadmap_item_id": link_roadmap_item_id,
        "workflow_stage_instance_id": link_workflow_stage_instance_id,
    }

    # --- 解析并处理 GitHub 链接 ---
    github_issue_number = None
    if link_github_issue:
        try:
            # 解析GitHub链接
            if "#" not in link_github_issue or "/" not in link_github_issue.split("#")[0]:
                raise ValueError("GitHub 链接格式应为 'owner/repo#number'")
            repo_part, issue_num_str = link_github_issue.split("#", 1)
            github_issue_number = int(issue_num_str)
            task_data["github_issue_number"] = github_issue_number
            logger.info(f"解析到 GitHub Issue 编号: {github_issue_number} (仓库: {repo_part})")
        except ValueError as e:
            results["status"] = "error"
            results["code"] = 400
            results["message"] = f"无效的 GitHub 链接格式: {e}"
            console.print(f"[bold red]错误:[/bold red] 无效的 GitHub 链接格式: {e}")
            return results
        except Exception as e:
            logger.error(f"解析 GitHub 链接时出错: {e}", exc_info=True)
            console.print(f"[bold red]错误:[/bold red] 解析 GitHub 链接时出错: {e}")
            return results

    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            task_repo = TaskRepository(session)
            # 使用 create_task 来处理 JSON 字段
            new_task = task_repo.create_task(task_data)
            session.commit()  # 需要 commit 来持久化

            task_dict = new_task.to_dict()
            results["data"] = task_dict
            results["message"] = f"成功创建任务 (ID: {new_task.id})"

            # --- 控制台输出 ---
            console.print(f"[bold green]成功:[/bold green] 已创建任务 '{new_task.title}' (ID: {new_task.id})")

    except ValueError as ve:  # 处理 Repository 中可能的 JSON 字段验证错误
        logger.error(f"创建任务时数据验证失败: {ve}", exc_info=True)
        results["status"] = "error"
        results["code"] = 400
        results["message"] = f"创建任务失败: {ve}"
        console.print(f"[bold red]错误:[/bold red] {ve}")
    except Exception as e:
        logger.error(f"创建任务时出错: {e}", exc_info=True)
        results["status"] = "error"
        results["code"] = 500
        results["message"] = f"创建任务时出错: {e}"
        console.print(f"[bold red]错误:[/bold red] {e}")

    return results
