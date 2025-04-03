"""
任务命令模块

处理任务相关命令。
"""

import argparse
from typing import Any, Dict

from scripts.github_roadmap.commands.command_base import CommandBase


class TaskCommand(CommandBase):
    """任务命令处理类"""

    def add_parser(self, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        添加任务命令解析器

        Args:
            subparsers: 子解析器集合

        Returns:
            argparse.ArgumentParser: 添加的解析器
        """
        parser = subparsers.add_parser("task", help="显示任务")
        parser.add_argument("--milestone", help="里程碑ID")
        parser.add_argument("--all", action="store_true", help="显示所有任务")
        return parser

    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        执行任务命令，用于查看特定里程碑下的任务

        Args:
            args: 命令行参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            roadmap = self.processor.read_roadmap()

            if args.milestone:
                # 查找特定里程碑下的任务
                milestone = roadmap.get_milestone_by_id(args.milestone)
                if not milestone:
                    return {"success": False, "error": f"未找到里程碑: {args.milestone}"}

                tasks = roadmap.get_tasks_by_milestone(args.milestone)

                return {
                    "success": True,
                    "milestone": milestone.name,
                    "tasks": [
                        {
                            "id": task.id,
                            "title": task.title,
                            "status": task.status,
                            "priority": task.priority,
                            "assignees": task.assignees,
                        }
                        for task in tasks
                    ],
                }

            elif args.all:
                # 返回所有任务
                return {
                    "success": True,
                    "tasks": [
                        {
                            "id": task.id,
                            "title": task.title,
                            "milestone": task.milestone,
                            "status": task.status,
                            "priority": task.priority,
                            "assignees": task.assignees,
                        }
                        for task in roadmap.tasks
                    ],
                }

            else:
                # 默认返回活跃里程碑下的任务
                active_milestone = None
                for milestone in roadmap.milestones:
                    if milestone.status == "in_progress":
                        active_milestone = milestone
                        break

                if not active_milestone:
                    return {"success": False, "error": "没有处于进行中的里程碑"}

                tasks = roadmap.get_tasks_by_milestone(active_milestone.id)

                return {
                    "success": True,
                    "milestone": active_milestone.name,
                    "tasks": [
                        {
                            "id": task.id,
                            "title": task.title,
                            "status": task.status,
                            "priority": task.priority,
                            "assignees": task.assignees,
                        }
                        for task in tasks
                    ],
                }

        except Exception as e:
            return {"success": False, "error": str(e)}
