"""
命令解析器模块

负责：
- 命令解析
- 参数验证
- 命令路由
"""

import logging
import sys
from typing import Any, Dict, List, Optional, Tuple

from src.cli.base_command import BaseCommand

logger = logging.getLogger(__name__)


class CommandParser:
    """命令解析器类"""

    def __init__(self):
        """初始化命令解析器"""
        self.commands = {}

    def parse_args(self, args: List[str]) -> Tuple[str, Dict[str, Any]]:
        """解析命令行参数

        Args:
            args: 命令行参数列表

        Returns:
            Tuple[str, Dict[str, Any]]: 命令名称和参数字典

        Raises:
            ValueError: 参数格式无效
        """
        if not args:
            raise ValueError("命令不能为空")

        command_name = args[0]
        parsed_args = {}

        i = 1
        while i < len(args):
            arg = args[i]
            if arg.startswith("--"):
                key = arg[2:]
                if "=" in key:
                    key, value = key.split("=", 1)
                    parsed_args[key] = value
                elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                    # 下一个参数不是选项，视为当前选项的值
                    parsed_args[key] = args[i + 1]
                    i += 1
                else:
                    # 布尔选项
                    parsed_args[key] = True
            i += 1

        return command_name, parsed_args

    def register_command(self, command: BaseCommand):
        """注册命令处理器

        Args:
            command: 命令处理器实例
        """
        self.commands[command.name] = command
        logger.info(f"已注册命令: {command.name}")

    def execute_command(self, command_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行命令

        Args:
            command_name: 命令名称
            args: 命令参数

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            if command_name not in self.commands:
                return {"success": False, "error": f"未知命令: {command_name}"}

            # 获取命令处理器并执行
            command_handler = self.commands[command_name]
            logger.debug(f"执行命令: {command_name}, 参数: {args}")
            return command_handler.execute(args)

        except Exception as e:
            error_msg = f"执行命令失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg, "error_type": type(e).__name__}

    def get_available_commands(self) -> List[Dict[str, str]]:
        """获取所有可用命令的列表

        Returns:
            List[Dict[str, str]]: 命令列表，包含名称和描述
        """
        return [
            {"name": name, "description": cmd.description} for name, cmd in self.commands.items()
        ]

    def get_command_help(self, command_name: str) -> Dict[str, Any]:
        """获取指定命令的帮助信息

        Args:
            command_name: 命令名称

        Returns:
            Dict[str, Any]: 命令帮助信息
        """
        if command_name not in self.commands:
            return {"success": False, "error": f"未知命令: {command_name}"}

        command = self.commands[command_name]
        return {
            "success": True,
            "command": command_name,
            "description": command.description,
            "usage": command.get_usage(),
            "examples": command.get_examples(),
        }

    def parse_and_execute(self, args: List[str]) -> int:
        """解析参数并执行命令

        Args:
            args: 命令行参数

        Returns:
            int: 执行结果代码，0表示成功
        """
        if not args:
            self._print_help()
            return 0

        command_name = args[0]

        # 处理帮助命令
        if command_name in ["-h", "--help", "help"]:
            if len(args) > 1:
                # 显示特定命令的帮助
                command_help = self.get_command_help(args[1])
                if command_help["success"]:
                    self._print_command_help(command_help)
                else:
                    print(f"错误: {command_help['error']}")
                    return 1
            else:
                # 显示通用帮助
                self._print_help()
            return 0

        # 执行命令
        if command_name not in self.commands:
            print(f"错误: 未知命令 '{command_name}'")
            self._print_help()
            return 1

        command_args = {}
        if len(args) > 1:
            try:
                _, command_args = self.parse_args(args)
            except ValueError as e:
                print(f"错误: {str(e)}")
                return 1

        result = self.execute_command(command_name, command_args)

        # 处理执行结果
        if result.get("success", False):
            if "message" in result:
                print(result["message"])

            # 如果有数据，以适当格式输出
            if "data" in result:
                output_format = command_args.get("format", "text")
                self._print_data(result["data"], output_format)

            return 0
        else:
            print(f"错误: {result.get('error', '未知错误')}")
            return 1

    def _print_help(self):
        """打印通用帮助信息"""
        print("VibeCopilot 命令行工具")
        print("\n可用命令:")

        commands = self.get_available_commands()
        for cmd in commands:
            print(f"  {cmd['name']:<12} - {cmd['description']}")

        print("\n使用 '<命令> --help' 获取特定命令的帮助")

    def _print_command_help(self, help_info: Dict[str, Any]):
        """打印特定命令的帮助信息"""
        print(f"\n命令: {help_info['command']}")
        print(f"描述: {help_info['description']}")
        print(f"\n用法: {help_info['usage']}")

        if help_info.get("examples"):
            print("\n示例:")
            for example in help_info["examples"]:
                print(f"  {example}")

    def _print_data(self, data: Any, format_type: str):
        """打印数据，根据格式类型选择不同的输出方式"""
        if format_type == "json":
            import json

            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            # 文本格式
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            print(f"{k}: {v}")
                        print()
                    else:
                        print(item)
            elif isinstance(data, dict):
                for k, v in data.items():
                    print(f"{k}: {v}")
            else:
                print(data)
