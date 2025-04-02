"""
路线图CLI模块

提供命令行接口，用于处理路线图相关命令。
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

from .github_sync import GitHubSync
from .models import Milestone, Roadmap, Task
from .roadmap_processor import RoadmapProcessor


class RoadmapCLI:
    """路线图命令行接口类"""

    def __init__(self):
        """初始化路线图CLI"""
        self.processor = RoadmapProcessor()
        self.github_sync = None

    def setup_github_sync(self, owner: str = None, repo: str = None):
        """
        设置GitHub同步工具

        Args:
            owner: 仓库所有者
            repo: 仓库名称
        """
        from ..api import GitHubClient

        client = GitHubClient()
        self.github_sync = GitHubSync(
            github_client=client,
            owner=owner or os.environ.get("GITHUB_OWNER"),
            repo=repo or os.environ.get("GITHUB_REPO"),
        )

    def handle_check_command(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        处理检查命令，显示路线图状态

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

    def handle_update_command(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        处理更新命令，更新任务或里程碑状态

        Args:
            args: 命令行参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            roadmap = self.processor.read_roadmap()

            if args.type == "task":
                if not args.id:
                    return {"success": False, "error": "未提供任务ID"}

                task = roadmap.get_task_by_id(args.id)
                if not task:
                    return {"success": False, "error": f"未找到任务: {args.id}"}

                # 更新任务状态
                roadmap = self.processor.update_task_status(
                    task_id=args.id, new_status=args.status, assignee=args.assignee
                )

                # 同步到GitHub
                if self.github_sync and args.sync:
                    self.github_sync.sync_task_to_github(task)

                return {"success": True, "message": f"已更新任务 {args.id} 状态为 {args.status}"}

            elif args.type == "milestone":
                if not args.id:
                    return {"success": False, "error": "未提供里程碑ID"}

                milestone = roadmap.get_milestone_by_id(args.id)
                if not milestone:
                    return {"success": False, "error": f"未找到里程碑: {args.id}"}

                # 更新里程碑状态
                roadmap = self.processor.update_milestone_status(
                    milestone_id=args.id, new_status=args.status
                )

                # 同步到GitHub
                if self.github_sync and args.sync:
                    self.github_sync.sync_milestone_to_github(milestone)

                return {"success": True, "message": f"已更新里程碑 {args.id} 状态为 {args.status}"}

            else:
                return {"success": False, "error": f"不支持的更新类型: {args.type}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def handle_story_command(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        处理用户故事命令，添加新故事/任务

        Args:
            args: 命令行参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            if not args.title:
                return {"success": False, "error": "缺少标题"}

            if args.type == "task":
                if not args.milestone:
                    return {"success": False, "error": "未指定所属里程碑"}

                task = self.processor.add_task(
                    title=args.title,
                    description=args.description or "",
                    milestone_id=args.milestone,
                    status="todo",
                    priority=args.priority or "P2",
                    assignees=args.assignees.split(",") if args.assignees else [],
                )

                # 同步到GitHub
                if self.github_sync and args.sync:
                    self.github_sync.sync_task_to_github(task)

                return {"success": True, "message": f"已添加任务 {task.id}", "task_id": task.id}

            elif args.type == "milestone":
                milestone = self.processor.add_milestone(
                    name=args.title,
                    description=args.description or "",
                    start_date=args.start_date,
                    end_date=args.end_date,
                    status="planned",
                )

                # 同步到GitHub
                if self.github_sync and args.sync:
                    self.github_sync.sync_milestone_to_github(milestone)

                return {
                    "success": True,
                    "message": f"已添加里程碑 {milestone.id}",
                    "milestone_id": milestone.id,
                }

            else:
                return {"success": False, "error": f"不支持的类型: {args.type}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def handle_task_command(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        处理任务命令，用于查看特定里程碑下的任务

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

    def handle_plan_command(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        处理计划命令，添加新的项目计划（里程碑）

        Args:
            args: 命令行参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            if not args.title:
                return {"success": False, "error": "缺少计划标题"}

            if args.type not in ["milestone", "phase"]:
                return {"success": False, "error": f"不支持的计划类型: {args.type}"}

            # 添加里程碑
            milestone = self.processor.add_milestone(
                name=args.title,
                description=args.description or "",
                start_date=args.start_date,
                end_date=args.end_date,
                status="planned",
            )

            # 同步到GitHub
            if self.github_sync and args.sync:
                self.github_sync.sync_milestone_to_github(milestone)

            return {
                "success": True,
                "message": f"已添加{args.type}计划 {milestone.id}",
                "milestone_id": milestone.id,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def handle_sync_command(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        处理同步命令，在roadmap.yaml和GitHub项目之间同步数据

        Args:
            args: 命令行参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        try:
            if not self.github_sync:
                self.setup_github_sync(args.owner, args.repo)

            if not self.github_sync:
                return {"success": False, "error": "GitHub同步未初始化"}

            roadmap = self.processor.read_roadmap()

            if args.direction == "to-github":
                milestones, tasks = self.github_sync.sync_roadmap_to_github(roadmap)

                return {
                    "success": True,
                    "message": f"已同步 {len(milestones)} 个里程碑和 {len(tasks)} 个任务到GitHub",
                    "milestones": len(milestones),
                    "tasks": len(tasks),
                }

            elif args.direction == "from-github":
                updated_roadmap = self.github_sync.sync_github_to_roadmap(roadmap)
                self.processor.write_roadmap(updated_roadmap)

                return {
                    "success": True,
                    "message": "已从GitHub同步路线图数据",
                    "milestones": len(updated_roadmap.milestones),
                    "tasks": len(updated_roadmap.tasks),
                }

            else:
                return {"success": False, "error": f"不支持的同步方向: {args.direction}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def parse_args(self, args: List[str] = None) -> argparse.Namespace:
        """
        解析命令行参数

        Args:
            args: 命令行参数列表

        Returns:
            argparse.Namespace: 解析后的参数
        """
        parser = argparse.ArgumentParser(description="路线图管理工具")
        subparsers = parser.add_subparsers(dest="command", help="子命令")

        # check命令
        check_parser = subparsers.add_parser("check", help="检查路线图状态")

        # update命令
        update_parser = subparsers.add_parser("update", help="更新任务或里程碑状态")
        update_parser.add_argument(
            "--type", choices=["task", "milestone"], required=True, help="更新类型"
        )
        update_parser.add_argument("--id", help="任务或里程碑ID")
        update_parser.add_argument("--status", help="新状态")
        update_parser.add_argument("--assignee", help="任务指派人")
        update_parser.add_argument("--sync", action="store_true", help="同步到GitHub")

        # story命令
        story_parser = subparsers.add_parser("story", help="添加用户故事/任务")
        story_parser.add_argument("--type", choices=["task", "milestone"], required=True, help="类型")
        story_parser.add_argument("--title", required=True, help="标题")
        story_parser.add_argument("--description", help="描述")
        story_parser.add_argument("--milestone", help="所属里程碑ID")
        story_parser.add_argument("--priority", choices=["P0", "P1", "P2", "P3"], help="优先级")
        story_parser.add_argument("--assignees", help="指派人，逗号分隔")
        story_parser.add_argument("--start-date", help="开始日期")
        story_parser.add_argument("--end-date", help="结束日期")
        story_parser.add_argument("--sync", action="store_true", help="同步到GitHub")

        # task命令
        task_parser = subparsers.add_parser("task", help="显示任务")
        task_parser.add_argument("--milestone", help="里程碑ID")
        task_parser.add_argument("--all", action="store_true", help="显示所有任务")

        # plan命令
        plan_parser = subparsers.add_parser("plan", help="添加项目计划")
        plan_parser.add_argument(
            "--type", choices=["milestone", "phase"], required=True, help="计划类型"
        )
        plan_parser.add_argument("--title", required=True, help="计划标题")
        plan_parser.add_argument("--description", help="计划描述")
        plan_parser.add_argument("--start-date", help="开始日期")
        plan_parser.add_argument("--end-date", help="结束日期")
        plan_parser.add_argument("--sync", action="store_true", help="同步到GitHub")

        # sync命令
        sync_parser = subparsers.add_parser("sync", help="同步数据")
        sync_parser.add_argument(
            "--direction", choices=["to-github", "from-github"], required=True, help="同步方向"
        )
        sync_parser.add_argument("--owner", help="GitHub仓库所有者")
        sync_parser.add_argument("--repo", help="GitHub仓库名称")

        return parser.parse_args(args)

    def run(self, args: List[str] = None) -> Dict[str, Any]:
        """
        运行CLI

        Args:
            args: 命令行参数列表

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        parsed_args = self.parse_args(args)

        if parsed_args.command == "check":
            return self.handle_check_command(parsed_args)
        elif parsed_args.command == "update":
            return self.handle_update_command(parsed_args)
        elif parsed_args.command == "story":
            return self.handle_story_command(parsed_args)
        elif parsed_args.command == "task":
            return self.handle_task_command(parsed_args)
        elif parsed_args.command == "plan":
            return self.handle_plan_command(parsed_args)
        elif parsed_args.command == "sync":
            return self.handle_sync_command(parsed_args)
        else:
            return {"success": False, "error": f"未知命令: {parsed_args.command}"}


def main():
    """CLI主入口"""
    cli = RoadmapCLI()
    result = cli.run(sys.argv[1:])

    if result.get("success"):
        if "message" in result:
            print(result["message"])
        else:
            print(result)
    else:
        print(f"错误: {result.get('error', '未知错误')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
