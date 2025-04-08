# src/cli/commands/task/task_create_command.py

import argparse
import logging
from typing import Any, Dict, List, Optional, Tuple

import typer
from rich.console import Console

from src.cli.commands.base_command import BaseCommand
from src.db import get_session_factory
from src.db.repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)
console = Console()


class CreateTaskCommand(BaseCommand):
    """创建新任务命令

    创建一个新的任务，支持设置标题、描述、负责人、标签等基本信息，
    以及关联到 Roadmap Item、Workflow Stage 或 GitHub Issue。

    选项:
        --title, -t: 任务标题 (必需)
        --desc, -d: 任务描述
        --assignee, -a: 负责人
        --label, -l: 标签 (可多次使用)
        --status, -s: 初始状态 (默认: open)
        --link-roadmap: 关联到 Story ID
        --link-workflow-stage: 关联到 Workflow Stage
        --link-github: 关联到 GitHub Issue (格式: owner/repo#number)
    """

    def __init__(self):
        super().__init__("create", "创建一个新的任务")

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """配置命令行解析器"""
        parser.add_argument("-t", "--title", required=True, help="任务标题 (必需)")
        parser.add_argument("-d", "--desc", help="任务描述")
        parser.add_argument("-a", "--assignee", help="负责人")
        parser.add_argument("-l", "--label", action="append", help="标签 (可多次使用)")
        parser.add_argument("-s", "--status", default="open", help="初始状态 (默认: open)")
        parser.add_argument("--link-roadmap", help="关联到 Roadmap Item (Story ID)")
        parser.add_argument("--link-workflow-stage", help="关联到 Workflow Stage Instance ID")
        parser.add_argument("--link-github", help="关联到 GitHub Issue (格式: owner/repo#number)")

    def execute_with_args(self, args: argparse.Namespace) -> int:
        """执行命令"""
        try:
            self.execute(
                title=args.title,
                description=args.desc,
                assignee=args.assignee,
                label=args.label,
                status=args.status,
                link_roadmap_item_id=args.link_roadmap,
                link_workflow_stage_instance_id=args.link_workflow_stage,
                link_github_issue=args.link_github,
            )
            return 0
        except Exception as e:
            logger.error(f"创建任务时出错: {e}", exc_info=True)
            console.print(f"[bold red]错误:[/bold red] {e}")
            return 1

    def execute(
        self,
        title: str,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        label: Optional[List[str]] = None,
        status: Optional[str] = "open",
        link_roadmap_item_id: Optional[str] = None,
        link_workflow_stage_instance_id: Optional[str] = None,
        link_github_issue: Optional[str] = None,
    ) -> Dict[str, Any]:
        """执行创建任务的逻辑"""
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
            },  # locals() might capture too much, refine if needed
        }

        task_data = {
            "title": title,
            "description": description,
            "assignee": assignee,
            "labels": label,  # labels are already List[str] from Typer
            "status": status,
            "roadmap_item_id": link_roadmap_item_id,
            "workflow_stage_instance_id": link_workflow_stage_instance_id,
        }

        # --- 解析并处理 GitHub 链接 ---
        github_issue_number = None
        if link_github_issue:
            try:
                # 这里不实际调用 github adapter，仅解析和存储 number
                # 实际验证可以在 link 命令或 adapter 中做
                if "#" not in link_github_issue or "/" not in link_github_issue.split("#")[0]:
                    raise ValueError("GitHub 链接格式应为 'owner/repo#number'")
                repo_part, issue_num_str = link_github_issue.split("#", 1)
                github_issue_number = int(issue_num_str)
                # 可以在这里存储 repo_part 到 task 数据中，如果需要的话
                task_data["github_issue_number"] = github_issue_number
                logger.info(f"解析到 GitHub Issue 编号: {github_issue_number} (仓库: {repo_part})")
            except ValueError as e:
                results["status"] = "error"
                results["code"] = 400
                results["message"] = f"无效的 GitHub 链接格式: {e}"
                if not self.is_agent_mode(locals()):
                    console.print(f"[bold red]错误:[/bold red] 无效的 GitHub 链接格式: {e}")
                return results
            except Exception as e:
                logger.error(f"解析 GitHub 链接时出错: {e}", exc_info=True)
                # Remove trailing space after backslash if any
                console.print(f"[bold red]错误:[/bold red] 解析 GitHub 链接时出错: {e}")
                return results

        try:
            session_factory = get_session_factory()
            with session_factory() as session:
                task_repo = TaskRepository(session)
                # 使用 create_task 而不是基类的 create 来处理 JSON 字段
                new_task = task_repo.create_task(task_data)
                session.commit()  # 需要 commit 来持久化

                task_dict = new_task.to_dict()
                results["data"] = task_dict
                results["message"] = f"成功创建任务 (ID: {new_task.id})"

                # --- 控制台输出 (非 Agent 模式) ---
                if not self.is_agent_mode(locals()):
                    console.print(f"[bold green]成功:[/bold green] 已创建任务 '{new_task.title}' (ID: {new_task.id})")
                    # 可以选择性地显示更多信息
                    # console.print(f"  状态: {new_task.status}")
                    # console.print(f"  负责人: {new_task.assignee if new_task.assignee else '-'}")

        except ValueError as ve:  # 处理 Repository 中可能的 JSON 字段验证错误
            logger.error(f"创建任务时数据验证失败: {ve}", exc_info=True)
            results["status"] = "error"
            results["code"] = 400
            results["message"] = f"创建任务失败: {ve}"
            if not self.is_agent_mode(locals()):
                console.print(f"[bold red]错误:[/bold red] {ve}")
        except Exception as e:
            logger.error(f"创建任务时出错: {e}", exc_info=True)
            # 捕获到异常时也应该回滚
            # if 'session' in locals() and session.is_active:
            #    session.rollback()
            results["status"] = "error"
            results["code"] = 500
            results["message"] = f"创建任务时出错: {e}"
            if not self.is_agent_mode(locals()):
                console.print(f"[bold red]错误:[/bold red] {e}")

        return results

    def is_agent_mode(self, args: Dict[str, Any]) -> bool:
        """检查是否处于 Agent 模式 (简化)"""
        return False

    def _extract_repo_and_issue(self, link: str) -> Optional[Tuple[str, int]]:
        # Implementation of _extract_repo_and_issue method
        pass
