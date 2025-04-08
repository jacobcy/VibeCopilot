"""
路线图管理命令模块

处理路线图相关的命令，包括创建、查看、更新、删除、同步和切换路线图等操作。
"""

import json
import logging
import os
from typing import Any, Dict, List

from rich.console import Console

from src.cli.base_command import BaseCommand
from src.cli.command import Command
from src.cli.commands.roadmap.core import RoadmapCommandExecutor, parse_roadmap_args
from src.db.service import DatabaseService
from src.roadmap import RoadmapService

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
        self.db_service = DatabaseService()

        # 初始化命令执行器
        self.command_executor = RoadmapCommandExecutor(service=self.service, db_service=self.db_service, db_path=self.db_path)

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
        return parse_roadmap_args(args)

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

        # 执行命令
        result = self._execute_impl(parsed_args)

        # 格式化输出
        if isinstance(result, dict):
            if result.get("success", False):
                # 输出结果
                if "message" in result:
                    console.print(f"[green]{result['message']}[/green]")

                # 输出数据
                if "data" in result:
                    data = result["data"]

                    # 格式化输出数据
                    if isinstance(data, list):
                        for item in data:
                            self._print_roadmap_item(item)
                    elif isinstance(data, dict):
                        # 对于字典类型的数据（如同步结果），也应该输出
                        for key, value in data.items():
                            console.print(f"[bold]{key}:[/bold] {value}")
                    else:
                        self._print_roadmap_item(data)
            else:
                # 输出错误
                error_message = result.get("error", "未知错误")
                console.print(f"[red]错误: {error_message}[/red]")

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        实现命令执行逻辑

        Args:
            args: 命令参数

        Returns:
            执行结果
        """
        # 判断是否是Agent模式
        args["agent_mode"] = self.is_agent_mode(args)

        # 使用命令执行器执行命令
        return self.command_executor.execute_command(args)

    def _print_roadmap_item(self, item: Any) -> None:
        """打印路线图项目"""
        if hasattr(item, "to_dict"):
            item = item.to_dict()

        if isinstance(item, dict):
            if "id" in item and "name" in item:
                console.print(f"[bold]ID:[/bold] {item['id']}")
                console.print(f"[bold]名称:[/bold] {item['name']}")

                if "description" in item:
                    console.print(f"[bold]描述:[/bold] {item['description']}")

                if "active" in item and item["active"]:
                    console.print("[bold green]当前活动路线图[/bold green]")

                console.print("-" * 50)
            else:
                # 其他类型的字典，直接打印键值对
                for key, value in item.items():
                    console.print(f"[bold]{key}:[/bold] {value}")
                console.print("-" * 50)
        else:
            # 非字典对象，直接打印字符串表示
            console.print(str(item))

    def is_agent_mode(self, args: Dict) -> bool:
        """
        判断是否在Agent模式下运行

        Args:
            args: 命令参数

        Returns:
            是否是Agent模式
        """
        # 根据环境变量或者参数判断是否是Agent模式
        # 这里简化实现
        return args.get("format") == "json" or os.environ.get("VIBECOPILOT_AGENT_MODE") == "1"
