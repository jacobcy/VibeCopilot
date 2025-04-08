# src/cli/commands/task/task_link_command.py

import argparse
import logging
import re
from enum import Enum
from typing import Any, Dict, Optional

import typer
from rich.console import Console

from src.cli.commands.base_command import BaseCommand
from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository
from src.models.db.task import Task  # For type hinting

logger = logging.getLogger(__name__)
console = Console()


class LinkType(str, Enum):
    """支持的链接类型枚举"""

    ROADMAP = "roadmap"
    WORKFLOW_STAGE = "workflow_stage"
    GITHUB_ISSUE = "github_issue"
    GITHUB_PR = "github_pr"
    GITHUB_COMMIT = "github_commit"


class LinkTaskCommand(BaseCommand):
    """关联任务到其他实体命令

    将任务关联到其他实体，如Roadmap Item、Workflow Stage或GitHub实体。
    支持添加和移除关联关系。对于GitHub实体，支持关联到Issue、PR和Commit。

    参数:
        task_id: 要关联的任务ID

    选项:
        --type, -t: 关联类型，可选值：
            - roadmap: 关联到Roadmap Item (Story)
            - workflow_stage: 关联到工作流阶段
            - github_issue: 关联到GitHub Issue
            - github_pr: 关联到GitHub Pull Request
            - github_commit: 关联到GitHub Commit
        --target, -id: 目标实体的标识符
            - 对于roadmap: Story ID
            - 对于workflow_stage: Stage Instance ID
            - 对于github_issue: owner/repo#issue_number
            - 对于github_pr: owner/repo#pr_number
            - 对于github_commit: owner/repo@commit_sha
            使用'-'表示取消关联

    示例:
        vibecopilot task link abc123 -t roadmap --target S1
        vibecopilot task link def456 -t github_issue --target owner/repo#123
        vibecopilot task link ghi789 -t github_pr --target owner/repo#456
        vibecopilot task link jkl012 -t github_commit --target owner/repo@abcdef123
        vibecopilot task link mno345 -t roadmap --target - # 取消关联
    """

    def __init__(self):
        super().__init__("link", "关联任务到 Roadmap Item, Workflow Stage 或 GitHub 实体")

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """配置命令的参数解析器"""
        parser.add_argument("task_id", help="要关联的 Task ID")
        parser.add_argument("-t", "--type", required=True, choices=[t.value for t in LinkType], help="要关联的目标实体类型")
        parser.add_argument("-id", "--target", required=True, help="目标实体的 ID 或标识符 ('-' 表示取消关联)")

    def execute_with_args(self, args: argparse.Namespace) -> Dict[str, Any]:
        """使用解析后的参数执行命令"""
        return self.execute(task_id=args.task_id, link_type=LinkType(args.type), target_id=args.target)

    def execute(
        self,
        task_id: str = typer.Argument(..., help="要关联的 Task ID"),
        link_type: LinkType = typer.Option(..., "--type", "-t", help="要关联的目标实体类型", case_sensitive=False),
        target_id: str = typer.Option(..., "--target", "-id", help="目标实体的 ID 或标识符 ('-' 表示取消关联)"),
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

                # 检查任务是否存在 (除非是移除链接，否则都需要检查)
                # 对于 add_linked_pr/commit, Repository 内部也会检查
                # task = task_repo.get_by_id(task_id)
                # if not task and not (link_type in [LinkType.GITHUB_PR, LinkType.GITHUB_COMMIT] and not unlink):
                #     results["status"] = "error"
                #     results["code"] = 404
                #     results["message"] = f"操作失败：未找到 Task ID: {task_id}"
                #     if not self.is_agent_mode(locals()):
                #         console.print(f"[bold red]错误:[/bold red] 未找到 Task ID: {task_id}")
                #     return results

                if link_type == LinkType.ROADMAP:
                    updated_task = task_repo.link_to_roadmap(task_id, target_value)
                    link_desc = f"Roadmap Item (Story ID: {target_value})" if not unlink else "Roadmap Item"

                elif link_type == LinkType.WORKFLOW_STAGE:
                    updated_task = task_repo.link_to_workflow_stage(task_id, target_value)
                    link_desc = f"Workflow Stage Instance (ID: {target_value})" if not unlink else "Workflow Stage Instance"

                elif link_type == LinkType.GITHUB_ISSUE:
                    issue_number = None
                    if not unlink:
                        repo_part, issue_num_str = self._parse_github_ref(target_value, "#")
                        issue_number = int(issue_num_str)
                        # 可以在此调用 github adapter 验证 repo_part 和 issue_number
                    updated_task = task_repo.link_to_github_issue(task_id, issue_number)
                    link_desc = f"GitHub Issue ({target_value})" if not unlink else "GitHub Issue"

                elif link_type == LinkType.GITHUB_PR:
                    if unlink:
                        repo_part, pr_num_str = self._parse_github_ref(target_value, "#")  # Unlink 也需要解析来找到要移除哪个
                        pr_number = int(pr_num_str)
                        updated_task = task_repo.remove_linked_pr(task_id, repo_part, pr_number)
                        link_desc = f"GitHub PR ({target_value})"
                    else:
                        repo_part, pr_num_str = self._parse_github_ref(target_value, "#")
                        pr_number = int(pr_num_str)
                        # 可以在此调用 github adapter 验证
                        updated_task = task_repo.add_linked_pr(task_id, repo_part, pr_number)
                        link_desc = f"GitHub PR ({target_value})"

                elif link_type == LinkType.GITHUB_COMMIT:
                    if unlink:
                        repo_part, sha = self._parse_github_ref(target_value, "@")  # 使用 @ 分隔 commit
                        updated_task = task_repo.remove_linked_commit(task_id, repo_part, sha)
                        link_desc = f"GitHub Commit ({target_value})"
                    else:
                        repo_part, sha = self._parse_github_ref(target_value, "@")
                        # 可以在此调用 github adapter 验证
                        updated_task = task_repo.add_linked_commit(task_id, repo_part, sha)
                        link_desc = f"GitHub Commit ({target_value})"
                else:
                    # Should be caught by Typer Enum validation, but as a safeguard
                    raise ValueError(f"不支持的链接类型: {link_type}")

                if not updated_task:
                    # Repository 方法可能在 Task 不存在时返回 None
                    results["status"] = "error"
                    results["code"] = 404
                    results["message"] = f"操作失败：未找到 Task ID: {task_id} 或关联操作内部出错。"
                    if not self.is_agent_mode(locals()):
                        console.print(f"[bold red]错误:[/bold red] 未找到 Task ID: {task_id} 或关联操作失败。")
                    return results

                session.commit()  # 提交更改

                results["data"] = updated_task.to_dict()  # 返回更新后的 Task
                action = "取消关联" if unlink else "关联"
                results["message"] = f"成功将任务 {task_id} {action}到 {link_desc}"

                # --- 控制台输出 (非 Agent 模式) ---
                if not self.is_agent_mode(locals()):
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
            # if 'session' in locals() and session.is_active:
            #    session.rollback()
            results["status"] = "error"
            results["code"] = 500
            results["message"] = f"关联任务时出错: {e}"
            if not self.is_agent_mode(locals()):
                console.print(f"[bold red]错误:[/bold red] {e}")

        return results

    def _parse_github_ref(self, ref: str, delimiter: str) -> tuple[str, str]:
        """解析 GitHub 引用 (e.g., owner/repo#123 or owner/repo@sha)"""
        if delimiter not in ref or "/" not in ref.split(delimiter)[0]:
            raise ValueError(f"GitHub 引用格式应为 'owner/repo{delimiter}identifier'")
        repo_part, identifier = ref.split(delimiter, 1)
        if not repo_part or not identifier:
            raise ValueError(f"GitHub 引用格式应为 'owner/repo{delimiter}identifier'")
        return repo_part, identifier

    def is_agent_mode(self, args: Dict[str, Any]) -> bool:
        """检查是否处于 Agent 模式 (简化)"""
        return False
