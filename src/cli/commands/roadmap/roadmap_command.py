"""
路线图管理命令模块

处理路线图相关的命令，包括创建、查看、更新、删除、同步和切换路线图等操作。
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

from src.cli.base_command import BaseCommand
from src.cli.command import Command
from src.cli.commands.roadmap.handlers.detail_handlers import RoadmapDetailHandlers
from src.cli.commands.roadmap.handlers.edit_handlers import RoadmapEditHandlers
from src.cli.commands.roadmap.handlers.list_handlers import RoadmapListHandlers
from src.cli.commands.roadmap.handlers.show_handler import handle_show_roadmap
from src.cli.commands.roadmap.handlers.status_handler import handle_roadmap_status
from src.cli.commands.roadmap.handlers.sync_handlers import RoadmapSyncHandlers

# --- Imports for Task Integration ---
from src.db import get_session_factory
from src.db.repositories.roadmap_repository import RoadmapRepository, StoryRepository
from src.db.repositories.task_repository import TaskRepository
from src.db.service import DatabaseService
from src.models.db.roadmap import Roadmap, Story
from src.models.db.task import Task
from src.roadmap import RoadmapService

# ----------------------------------

logger = logging.getLogger(__name__)
console = Console()


class RoadmapCommand(BaseCommand, Command):
    """路线图管理命令处理器"""

    def __init__(self):
        super().__init__("roadmap", "路线图管理命令")
        self.service = RoadmapService()
        self.db_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, "roadmap.db")
        self.db_service = DatabaseService(self.db_path)

    # 实现新接口
    @classmethod
    def get_command(cls) -> str:
        return "roadmap"

    @classmethod
    def get_description(cls) -> str:
        return "路线图管理命令"

    @classmethod
    def get_help(cls) -> str:
        return """
路线图管理命令

用法:
    roadmap list [--verbose]                列出所有路线图
    roadmap show <id> [--format=<json|text>]        查看路线图详情
    roadmap create --name=<n> [--desc=<description>]    创建路线图
    roadmap update <id> [--name=<n>] [--desc=<description>]  更新路线图
    roadmap delete <id> [--force]                  删除路线图
    roadmap sync [--source=<source>] [--verbose]          同步路线图数据
    roadmap switch <id>                            切换活动路线图
    roadmap status <id>                            查看路线图状态

参数:
    <id>                       路线图ID

选项:
    --name=<n>              路线图名称
    --desc=<description>       路线图描述
    --format=<format>          输出格式 (json或text)
    --source=<source>          同步来源 (github或yaml)
    --force                    强制执行危险操作
    --verbose                  显示详细信息
"""

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parsed = {"command": self.get_command()}

        # 处理帮助选项
        if not args or "--help" in args or "-h" in args:
            parsed["show_help"] = True
            return parsed

        # 处理路线图操作
        roadmap_action = args.pop(0)
        parsed["roadmap_action"] = roadmap_action

        # 通用选项
        parsed["verbose"] = "--verbose" in args
        if "--verbose" in args:
            args.remove("--verbose")

        # 处理格式选项
        for i, arg in enumerate(args):
            if arg == "--format" and i + 1 < len(args):
                parsed["format"] = args[i + 1]
                args[i : i + 2] = []
                break
            elif arg.startswith("--format="):
                parsed["format"] = arg.split("=", 1)[1]
                args.remove(arg)
                break

        # 根据不同操作处理参数
        if roadmap_action == "list":
            # 不需要额外处理
            pass
        elif roadmap_action == "show":
            # 处理show参数
            if args:
                parsed["id"] = args.pop(0)
        elif roadmap_action == "create":
            # 处理create参数
            for i, arg in enumerate(args):
                if arg.startswith("--name="):
                    parsed["name"] = arg.split("=", 1)[1]
                    args.remove(arg)
                    break
                elif arg == "--name" and i + 1 < len(args):
                    parsed["name"] = args[i + 1]
                    args[i : i + 2] = []
                    break

            for i, arg in enumerate(args):
                if arg.startswith("--desc="):
                    parsed["description"] = arg.split("=", 1)[1]
                    args.remove(arg)
                    break
                elif arg == "--desc" and i + 1 < len(args):
                    parsed["description"] = args[i + 1]
                    args[i : i + 2] = []
                    break
        elif roadmap_action == "update":
            # 处理update参数
            if args and not args[0].startswith("--"):
                parsed["id"] = args.pop(0)

            # 解析name和description参数
            for i, arg in enumerate(args):
                if arg.startswith("--name="):
                    parsed["name"] = arg.split("=", 1)[1]
                    args.remove(arg)
                    break
                elif arg == "--name" and i + 1 < len(args):
                    parsed["name"] = args[i + 1]
                    args[i : i + 2] = []
                    break

            for i, arg in enumerate(args):
                if arg.startswith("--desc="):
                    parsed["description"] = arg.split("=", 1)[1]
                    args.remove(arg)
                    break
                elif arg == "--desc" and i + 1 < len(args):
                    parsed["description"] = args[i + 1]
                    args[i : i + 2] = []
                    break
        elif roadmap_action == "delete":
            # 处理delete参数
            if args and not args[0].startswith("--"):
                parsed["id"] = args.pop(0)
            parsed["force"] = "--force" in args
            if "--force" in args:
                args.remove("--force")
        elif roadmap_action == "sync":
            # 处理sync参数
            for i, arg in enumerate(args):
                if arg.startswith("--source="):
                    parsed["source"] = arg.split("=", 1)[1]
                    args.remove(arg)
                    break
                elif arg == "--source" and i + 1 < len(args):
                    parsed["source"] = args[i + 1]
                    args[i : i + 2] = []
                    break
        elif roadmap_action == "switch":
            # 处理switch参数
            if args:
                parsed["id"] = args.pop(0)
        elif roadmap_action == "status":
            # 处理status参数
            if args:
                parsed["id"] = args.pop(0)

        return parsed

    def execute(self, args) -> None:
        """执行命令 - 适配新接口"""
        # 处理参数
        parsed_args = {}
        if isinstance(args, list):
            # 如果是列表参数，首先解析成字典
            if not args or "--help" in args or "-h" in args:
                print(self.get_help())
                return
            parsed_args = self.parse_args(args)
        elif isinstance(args, dict):
            # 如果已经是字典，直接使用
            parsed_args = args
            # 处理帮助标识
            if not parsed_args or parsed_args.get("show_help", False):
                print(self.get_help())
                return
        else:
            # 不支持其他类型参数
            print("错误: 不支持的参数类型")
            return

        # 处理字典参数
        roadmap_action = parsed_args.get("roadmap_action")

        # 执行对应命令
        if roadmap_action == "list":
            result = self._list_roadmaps(parsed_args)
        elif roadmap_action == "show":
            result = self._show_roadmap(parsed_args)
        elif roadmap_action == "create":
            result = self._create_roadmap(parsed_args)
        elif roadmap_action == "update":
            result = self._update_roadmap(parsed_args)
        elif roadmap_action == "delete":
            result = self._delete_roadmap(parsed_args)
        elif roadmap_action == "sync":
            result = self._sync_roadmap(parsed_args)
        elif roadmap_action == "switch":
            result = self._switch_roadmap(parsed_args)
        elif roadmap_action == "status":
            result = self._roadmap_status(parsed_args)
        else:
            logger.error("未知的路线图操作: %s", roadmap_action)
            result = {"success": False, "error": f"未知的路线图操作: {roadmap_action}"}

        # 格式化输出
        if isinstance(result, dict):
            if result.get("success", False):
                # 输出结果
                if "message" in result:
                    print(result["message"])
                elif "data" in result:
                    # 格式化输出
                    output_format = parsed_args.get("format", "text")
                    if output_format == "json":
                        print(json.dumps(result["data"], ensure_ascii=False, indent=2))
                    else:
                        if isinstance(result["data"], dict):
                            for k, v in result["data"].items():
                                print(f"{k}: {v}")
                        elif isinstance(result["data"], list):
                            for item in result["data"]:
                                print(item)
                        else:
                            print(result["data"])
            else:
                # 输出错误
                if "error" in result:
                    print(f"错误: {result['error']}")
                else:
                    print("执行失败")

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """实际执行命令逻辑的分派"""
        action = args.get("roadmap_action")
        results = {"status": "error", "code": 1, "message": f"未知路线图操作: {action}", "data": None}

        try:
            if action == "list":
                results = self._list_roadmaps(args)
            elif action == "show":
                results = self._show_roadmap(args)
            elif action == "create":
                results = self._create_roadmap(args)
            elif action == "update":
                results = self._update_roadmap(args)
            elif action == "delete":
                results = self._delete_roadmap(args)
            elif action == "sync":
                results = self._sync_roadmap(args)
            elif action == "switch":
                results = self._switch_roadmap(args)
            elif action == "status":
                results = self._roadmap_status(args)
            else:
                logger.warning(f"未知的 roadmap action: {action}")
                # Return help or error message?
                results["message"] = f"未知路线图操作: {action}. 使用 --help 查看可用操作。"

        except Exception as e:
            logger.exception(f"执行 roadmap 操作 '{action}' 时出错: {e}")
            results["message"] = f"执行 roadmap 操作时出错: {e}"
            results["code"] = 500
            # Optionally print to console if not agent mode
            # if not self.is_agent_mode(args):
            #     console.print(f"[bold red]错误:[/bold red] {e}")

        # Standardized result structure for Agent
        final_result = {
            "status": results.get("status", "error" if results.get("code", 1) != 0 else "success"),
            "code": results.get("code", 1 if results.get("status", "error") == "error" else 0),
            "message": results.get("message", ""),
            "data": results.get("data", None),
            "meta": {"command": f"roadmap {action}", "args": args},
        }
        return final_result

    # 各个子命令的路由方法
    def _list_roadmaps(self, args: Dict) -> Dict[str, Any]:
        """处理 list 子命令"""
        logger.info("列出所有路线图...")
        session_factory = get_session_factory()
        with session_factory() as session:
            repo = RoadmapRepository(session)
            roadmaps = repo.get_all()
            roadmap_list = [rm.to_dict() for rm in roadmaps]
            # Console output (if not agent mode)
            if not self.is_agent_mode(args):
                if not roadmaps:
                    console.print("[yellow]没有找到任何路线图。[/yellow]")
                else:
                    table = Table(title="路线图列表")
                    table.add_column("ID", style="dim")
                    table.add_column("名称", style="bold cyan")
                    table.add_column("状态", style="magenta")
                    if args.get("verbose"):
                        table.add_column("描述")
                    for rm in roadmaps:
                        row = [rm.id, rm.name, rm.status]
                        if args.get("verbose"):
                            row.append(rm.description or "-")
                        table.add_row(*row)
                    console.print(table)

            return {
                "status": "success",
                "code": 0,
                "message": f"找到 {len(roadmap_list)} 个路线图",
                "data": roadmap_list,
            }

    def _show_roadmap(self, args: Dict) -> Dict[str, Any]:
        """处理 show 子命令 - 调用外部 handler"""
        return handle_show_roadmap(args, self.is_agent_mode(args))

    def _create_roadmap(self, args: Dict) -> Dict[str, Any]:
        """创建路线图"""
        return RoadmapEditHandlers.create_roadmap(self.service, args)

    def _update_roadmap(self, args: Dict) -> Dict[str, Any]:
        """更新路线图"""
        return RoadmapEditHandlers.update_roadmap(self.service, self.db_service, args)

    def _delete_roadmap(self, args: Dict) -> Dict[str, Any]:
        """删除路线图"""
        return RoadmapEditHandlers.delete_roadmap(self.service, self.db_service, args)

    def _sync_roadmap(self, args: Dict) -> Dict[str, Any]:
        """同步路线图数据"""
        return RoadmapSyncHandlers.sync_roadmap(self.service, args)

    def _switch_roadmap(self, args: Dict) -> Dict[str, Any]:
        """切换活动路线图"""
        return RoadmapSyncHandlers.switch_roadmap(self.service, self.db_service, args)

    def _roadmap_status(self, args: Dict) -> Dict[str, Any]:
        """处理 status 子命令 - 调用外部 handler"""
        return handle_roadmap_status(args, self.is_agent_mode(args))

    def is_agent_mode(self, args: Dict) -> bool:
        """检查是否处于 Agent 模式 (简化)"""
        # Based on args or environment? For now, assume False
        return False


# Register command (if using a central registry)
# CommandRegistry.register(RoadmapCommand)
