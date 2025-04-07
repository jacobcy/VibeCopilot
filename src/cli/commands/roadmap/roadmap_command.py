"""
路线图管理命令模块

处理路线图相关的命令，包括创建、查看、更新、删除、同步和切换路线图等操作。
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from src.cli.base_command import BaseCommand
from src.cli.command import Command
from src.cli.commands.roadmap.handlers.detail_handlers import RoadmapDetailHandlers
from src.cli.commands.roadmap.handlers.edit_handlers import RoadmapEditHandlers
from src.cli.commands.roadmap.handlers.list_handlers import RoadmapListHandlers
from src.cli.commands.roadmap.handlers.sync_handlers import RoadmapSyncHandlers
from src.db.service import DatabaseService
from src.roadmap import RoadmapService

logger = logging.getLogger(__name__)


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
        """实现BaseCommand接口的执行方法"""
        # 解析参数
        roadmap_action = args.get("roadmap_action")

        # 根据操作调用对应处理函数
        if roadmap_action == "list":
            result = self._list_roadmaps(args)
        elif roadmap_action == "show":
            result = self._show_roadmap(args)
        elif roadmap_action == "create":
            result = self._create_roadmap(args)
        elif roadmap_action == "update":
            result = self._update_roadmap(args)
        elif roadmap_action == "delete":
            result = self._delete_roadmap(args)
        elif roadmap_action == "sync":
            result = self._sync_roadmap(args)
        elif roadmap_action == "switch":
            result = self._switch_roadmap(args)
        elif roadmap_action == "status":
            result = self._roadmap_status(args)
        else:
            return {"success": False, "error": f"未知的路线图操作: {roadmap_action}"}

        return result

    # 各个子命令的路由方法
    def _list_roadmaps(self, args: Dict) -> Dict[str, Any]:
        """列出所有路线图"""
        return RoadmapListHandlers.list_roadmaps(self.db_service, args)

    def _show_roadmap(self, args: Dict) -> Dict[str, Any]:
        """显示路线图详情"""
        return RoadmapDetailHandlers.show_roadmap(self.db_service, args)

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
        """查看路线图状态"""
        return RoadmapSyncHandlers.roadmap_status(self.service, self.db_service, args)
