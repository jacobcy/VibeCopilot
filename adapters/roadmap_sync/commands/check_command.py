"""
检查命令模块

处理路线图状态检查相关命令。
"""

import argparse
from typing import Any, Dict

from scripts.github_roadmap.commands.command_base import CommandBase


class CheckCommand(CommandBase):
    """检查命令处理类"""

    def add_parser(self, subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        添加检查命令解析器

        Args:
            subparsers: 子解析器集合

        Returns:
            argparse.ArgumentParser: 添加的解析器
        """
        parser = subparsers.add_parser("check", help="检查路线图状态")
        return parser

    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        执行检查命令，显示路线图状态

        Args:
            args: 命令行参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            roadmap = self.processor.read_roadmap()

            result = {
                "success": True,
                "milestones": len(roadmap.milestones),
                "tasks": len(roadmap.tasks),
                "active_milestone": None,
                "milestone_status": {},
                "task_status": {"todo": 0, "in_progress": 0, "completed": 0},
            }

            # 计算各状态数量
            for task in roadmap.tasks:
                if task.status in result["task_status"]:
                    result["task_status"][task.status] += 1

            # 计算里程碑状态
            for milestone in roadmap.milestones:
                result["milestone_status"][milestone.id] = {
                    "name": milestone.name,
                    "status": milestone.status,
                    "progress": milestone.progress,
                    "tasks": len([t for t in roadmap.tasks if t.milestone == milestone.id]),
                }

                # 确定当前活跃里程碑
                if milestone.status == "in_progress":
                    result["active_milestone"] = milestone.id

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}
