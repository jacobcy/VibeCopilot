"""
VibeCopilot命令系统模块

处理Cursor IDE中的命令执行逻辑。
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from src.github.roadmap.cli import RoadmapCLI
from src.github.roadmap.roadmap_processor import RoadmapProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CommandProcessor:
    """处理VibeCopilot命令的类"""

    def __init__(self, project_path: Optional[str] = None) -> None:
        """
        初始化命令处理器

        Args:
            project_path: 项目路径，如果为None则使用当前目录
        """
        self.project_path = project_path or os.getcwd()
        self.status_file = os.path.join(self.project_path, ".ai", "status.json")
        self.roadmap_cli = RoadmapCLI()
        self.roadmap_processor = RoadmapProcessor()

    def _load_status(self) -> Dict[str, Any]:
        """
        加载项目状态

        Returns:
            Dict[str, Any]: 项目状态
        """
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logger.warning(f"状态文件不存在: {self.status_file}")
                return {}
        except Exception as e:
            logger.error(f"加载状态文件失败: {e}")
            return {}

    def _save_status(self, status: Dict[str, Any]) -> bool:
        """
        保存项目状态

        Args:
            status: 项目状态

        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)

            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(status, f, ensure_ascii=False, indent=2)

            logger.info(f"状态已保存到: {self.status_file}")
            return True
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
            return False

    def process_command(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理命令

        Args:
            command: 命令名称
            args: 命令参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        logger.info(f"处理命令: {command}, 参数: {args}")

        if command == "check":
            return self.handle_check_command(args)
        elif command == "update":
            return self.handle_update_command(args)
        elif command == "story":
            return self.handle_story_command(args)
        elif command == "task":
            return self.handle_task_command(args)
        elif command == "plan":
            return self.handle_plan_command(args)
        elif command == "sync":
            return self.handle_sync_command(args)
        else:
            return {"success": False, "error": f"未知命令: {command}"}

    def handle_check_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理检查命令

        Args:
            args: 命令参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        # 检查项目状态
        status = self._load_status()

        # 检查路线图状态
        try:
            roadmap_result = self.roadmap_cli.handle_check_command(None)

            # 合并结果
            result = {
                "success": True,
                "project": status.get("project", {}),
                "active_epic": status.get("active_epic", None),
                "active_story": status.get("active_story", None),
                "roadmap": roadmap_result,
            }

            return result
        except Exception as e:
            logger.error(f"处理check命令失败: {e}")
            return {"success": False, "error": f"处理命令失败: {e}"}

    def handle_update_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理更新命令

        Args:
            args: 命令参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        # 加载当前状态
        status = self._load_status()

        if args.get("type") == "task":
            task_id = args.get("id")
            new_status = args.get("status")
            assignee = args.get("assignee")

            if not task_id:
                return {"success": False, "error": "未提供任务ID"}

            # 更新状态文件中的任务状态
            updated = False
            if "tasks" in status:
                if task_id in status["tasks"]:
                    if new_status:
                        status["tasks"][task_id]["status"] = new_status
                    if assignee:
                        status["tasks"][task_id]["assignee"] = assignee

                    # 更新活动任务
                    if new_status == "in_progress":
                        status["active_task"] = task_id
                    elif status.get("active_task") == task_id and new_status == "completed":
                        status["active_task"] = None

                    updated = True

            # 如果任务不存在，给出错误消息
            if not updated:
                return {"success": False, "error": f"任务不存在: {task_id}"}

            # 保存状态
            if not self._save_status(status):
                return {"success": False, "error": "保存状态失败"}

            # 同时更新roadmap中的任务
            try:
                roadmap_result = self.roadmap_cli.run(
                    ["update", "--type", "task", "--id", task_id, "--status", new_status]
                )

                return {
                    "success": True,
                    "message": f"已更新任务 {task_id} 状态为 {new_status}",
                    "roadmap_sync": roadmap_result.get("success", False),
                }
            except Exception as e:
                logger.error(f"更新roadmap中的任务失败: {e}")
                return {
                    "success": True,
                    "message": f"已更新任务 {task_id} 状态为 {new_status}",
                    "roadmap_sync": False,
                    "roadmap_error": str(e),
                }

        elif args.get("type") == "story":
            story_id = args.get("id")
            new_status = args.get("status")

            if not story_id:
                return {"success": False, "error": "未提供故事ID"}

            # 更新状态文件中的故事状态
            if "stories" in status:
                if story_id in status["stories"]:
                    if new_status:
                        status["stories"][story_id]["status"] = new_status

                    # 更新活动故事
                    if new_status == "in_progress":
                        status["active_story"] = story_id
                    elif status.get("active_story") == story_id and new_status == "completed":
                        status["active_story"] = None

                    # 保存状态
                    if not self._save_status(status):
                        return {"success": False, "error": "保存状态失败"}

                    return {"success": True, "message": f"已更新故事 {story_id} 状态为 {new_status}"}
                else:
                    return {"success": False, "error": f"故事不存在: {story_id}"}
            else:
                return {"success": False, "error": "状态文件中没有故事信息"}

        else:
            return {"success": False, "error": f"不支持的更新类型: {args.get('type')}"}

    def handle_story_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理故事命令，添加新故事/任务

        Args:
            args: 命令参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        # 加载当前状态
        status = self._load_status()

        # 生成新故事或任务数据
        if args.get("type") == "task":
            # 确保必需参数
            if not args.get("title"):
                return {"success": False, "error": "未提供任务标题"}

            # 确保milestone参数存在
            milestone = args.get("milestone")

            # 添加到roadmap
            roadmap_args = [
                "story",
                "--type",
                "task",
                "--title",
                args.get("title"),
            ]

            # 添加可选参数
            if args.get("description"):
                roadmap_args.extend(["--description", args.get("description")])
            if milestone:
                roadmap_args.extend(["--milestone", milestone])
            if args.get("priority"):
                roadmap_args.extend(["--priority", args.get("priority")])
            if args.get("assignees"):
                roadmap_args.extend(["--assignees", args.get("assignees")])

            # 调用roadmap CLI添加任务
            try:
                roadmap_result = self.roadmap_cli.run(roadmap_args)

                # 如果成功添加到roadmap
                if roadmap_result.get("success"):
                    task_id = roadmap_result.get("task_id")

                    # 同时添加到状态文件
                    if not "tasks" in status:
                        status["tasks"] = {}

                    # 添加任务数据
                    status["tasks"][task_id] = {
                        "title": args.get("title"),
                        "description": args.get("description", ""),
                        "status": "todo",
                        "priority": args.get("priority", "P2"),
                        "assignee": args.get("assignees", "").split(",")[0]
                        if args.get("assignees")
                        else None,
                        "story": args.get("story", status.get("active_story")),
                        "epic": args.get("epic", status.get("active_epic")),
                    }

                    # 计算总任务数和各状态任务数
                    tasks_count = {
                        "total": len(status["tasks"]),
                        "todo": sum(1 for t in status["tasks"].values() if t["status"] == "todo"),
                        "in_progress": sum(
                            1 for t in status["tasks"].values() if t["status"] == "in_progress"
                        ),
                        "completed": sum(
                            1 for t in status["tasks"].values() if t["status"] == "completed"
                        ),
                    }

                    # 更新状态
                    status["tasks_count"] = tasks_count

                    # 保存状态
                    if not self._save_status(status):
                        return {
                            "success": True,
                            "message": f"已添加任务 {task_id}，但保存状态失败",
                            "task_id": task_id,
                        }

                    return {"success": True, "message": f"已添加任务 {task_id}", "task_id": task_id}
                else:
                    return roadmap_result

            except Exception as e:
                logger.error(f"添加任务到roadmap失败: {e}")
                return {"success": False, "error": f"添加任务失败: {e}"}

        elif args.get("type") == "story":
            # 确保必需参数
            if not args.get("title"):
                return {"success": False, "error": "未提供故事标题"}

            # 生成故事ID
            story_id = f"Story-{len(status.get('stories', {})) + 1}"

            # 添加故事数据
            if not "stories" in status:
                status["stories"] = {}

            status["stories"][story_id] = {
                "title": args.get("title"),
                "description": args.get("description", ""),
                "status": "todo",
                "epic": args.get("epic", status.get("active_epic")),
            }

            # 设置为活动故事
            status["active_story"] = story_id

            # 保存状态
            if not self._save_status(status):
                return {"success": False, "error": "保存状态失败"}

            return {"success": True, "message": f"已添加故事 {story_id}", "story_id": story_id}

        else:
            return {"success": False, "error": f"不支持的类型: {args.get('type')}"}

    def handle_task_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理任务命令，列出或查询任务

        Args:
            args: 命令参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        # 检查是否是查看特定故事或里程碑下的任务
        story_id = args.get("story")
        milestone_id = args.get("milestone")

        if story_id:
            # 查询特定故事下的任务
            status = self._load_status()

            if not "stories" in status or not story_id in status.get("stories", {}):
                return {"success": False, "error": f"故事不存在: {story_id}"}

            # 筛选任务
            tasks = {}
            for task_id, task in status.get("tasks", {}).items():
                if task.get("story") == story_id:
                    tasks[task_id] = task

            return {"success": True, "story": status["stories"][story_id], "tasks": tasks}

        elif milestone_id:
            # 使用roadmap CLI查询特定里程碑下的任务
            try:
                roadmap_args = ["task", "--milestone", milestone_id]
                roadmap_result = self.roadmap_cli.run(roadmap_args)
                return roadmap_result
            except Exception as e:
                logger.error(f"查询里程碑任务失败: {e}")
                return {"success": False, "error": f"查询任务失败: {e}"}

        else:
            # 默认返回所有活动任务
            try:
                status = self._load_status()
                active_story = status.get("active_story")

                if active_story:
                    # 筛选属于当前活动故事的任务
                    tasks = {}
                    for task_id, task in status.get("tasks", {}).items():
                        if task.get("story") == active_story:
                            tasks[task_id] = task

                    return {
                        "success": True,
                        "active_story": active_story,
                        "story_title": status.get("stories", {})
                        .get(active_story, {})
                        .get("title", ""),
                        "tasks": tasks,
                    }
                else:
                    # 如果没有活动故事，使用roadmap CLI返回活动里程碑下的任务
                    roadmap_result = self.roadmap_cli.run(["task"])
                    return roadmap_result

            except Exception as e:
                logger.error(f"查询任务失败: {e}")
                return {"success": False, "error": f"查询任务失败: {e}"}

    def handle_plan_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理计划命令，添加项目计划

        Args:
            args: 命令参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        plan_type = args.get("type", "milestone")
        title = args.get("title")

        if not title:
            return {"success": False, "error": "未提供计划标题"}

        # 构建roadmap CLI参数
        roadmap_args = ["plan", "--type", plan_type, "--title", title]

        # 添加可选参数
        if args.get("description"):
            roadmap_args.extend(["--description", args.get("description")])
        if args.get("start_date"):
            roadmap_args.extend(["--start-date", args.get("start_date")])
        if args.get("end_date"):
            roadmap_args.extend(["--end-date", args.get("end_date")])

        # 调用roadmap CLI添加计划
        try:
            roadmap_result = self.roadmap_cli.run(roadmap_args)
            return roadmap_result
        except Exception as e:
            logger.error(f"添加计划失败: {e}")
            return {"success": False, "error": f"添加计划失败: {e}"}

    def handle_sync_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理同步命令，在系统间同步数据

        Args:
            args: 命令参数

        Returns:
            Dict[str, Any]: 命令执行结果
        """
        # 同步类型和方向
        sync_type = args.get("type", "github")
        direction = args.get("direction", "to-github")

        if sync_type == "github":
            # 构建roadmap CLI参数
            roadmap_args = ["sync", "--direction", direction]

            # 添加可选参数
            if args.get("owner"):
                roadmap_args.extend(["--owner", args.get("owner")])
            if args.get("repo"):
                roadmap_args.extend(["--repo", args.get("repo")])

            # 调用roadmap CLI同步数据
            try:
                roadmap_result = self.roadmap_cli.run(roadmap_args)
                return roadmap_result
            except Exception as e:
                logger.error(f"同步GitHub数据失败: {e}")
                return {"success": False, "error": f"同步GitHub数据失败: {e}"}
        else:
            return {"success": False, "error": f"不支持的同步类型: {sync_type}"}


# 命令处理器实例
cmd_processor = CommandProcessor()


def process_command(command: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理命令的全局函数

    Args:
        command: 命令名称
        args: 命令参数

    Returns:
        Dict[str, Any]: 命令执行结果
    """
    return cmd_processor.process_command(command, args)
