"""
模板命令处理类

处理模板相关的命令，包括列表、查看、创建、更新、删除、导入、导出和生成等操作
"""

import json
import logging
from typing import Any, Dict, List

from rich.console import Console

from src.cli.base_command import BaseCommand
from src.cli.command import Command
from src.cli.commands.template.core import TemplateCommandExecutor, parse_template_args
from src.db import get_session_factory
from src.templates.core.template_manager import TemplateManager

logger = logging.getLogger(__name__)
console = Console()


class TemplateCommand(BaseCommand, Command):
    """模板命令处理器"""

    def __init__(self):
        super().__init__("template", "模板管理命令")
        # 使用会话工厂创建会话并初始化TemplateManager
        session_factory = get_session_factory()
        session = session_factory()
        self.manager = TemplateManager(session)
        self._session = session  # 保存会话以便在析构时关闭

        # 初始化命令执行器
        self.command_executor = TemplateCommandExecutor(manager=self.manager)

    def __del__(self):
        """析构函数，确保会话被关闭"""
        if hasattr(self, "_session"):
            try:
                self._session.close()
            except Exception:
                pass

    # 实现Command接口
    @classmethod
    def get_command(cls) -> str:
        return "template"

    @classmethod
    def get_description(cls) -> str:
        return "模板管理命令，提供模板的增删改查和生成功能"

    @classmethod
    def get_help(cls) -> str:
        return """
模板管理命令

用法:
    template list [--type=<template_type>] [--verbose]        列出所有模板
    template show <id> [--format=<json|text>]                 查看模板详情
    template create --name=<n> --type=<template_type>      创建模板
    template update <id> [--name=<n>]                      更新模板
    template delete <id> [--force]                            删除模板
    template import <file_path> [--overwrite] [--recursive]   导入模板
    template export <id> [--output=<path>] [--format=<format>]导出模板
    template generate <id> <output_file> [--vars=<json>]      使用模板生成内容
    template init [--force] [--source=<dir>]                  初始化模板库

参数:
    <id>                       模板ID或名称
    <file_path>                模板文件路径
    <output_file>              输出文件路径

选项:
    --name=<n>              模板名称
    --type=<template_type>     模板类型 (rule|command|doc|flow|roadmap|general)
    --format=<json|text>       输出格式
    --output=<path>            输出文件路径
    --vars=<json>              变量JSON字符串
    --overwrite                覆盖已存在的模板
    --recursive                递归导入目录下的所有模板
    --force                    强制执行危险操作，不提示确认
    --verbose                  显示详细信息
    --source=<dir>             指定源目录
"""

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        return parse_template_args(args)

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

        # 执行命令
        result = self._execute_impl(parsed_args)

        # 处理执行结果
        self._process_result(result, parsed_args)

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        实现命令执行逻辑

        Args:
            args: 命令参数

        Returns:
            执行结果
        """
        return self.command_executor.execute_command(args)

    def _process_result(self, result: Dict[str, Any], args: Dict[str, Any]) -> None:
        """
        处理命令执行结果

        Args:
            result: 执行结果
            args: 原始参数
        """
        # 如果结果中已经包含了格式化输出的标记，跳过输出
        if result.get("formatted", False) or result.get("table", False):
            return

        # 处理执行结果
        if result.get("success", False):
            # 如果有消息，输出消息
            if "message" in result:
                console.print(f"[green]{result['message']}[/green]")

            # 如果有数据，格式化输出数据
            if "data" in result:
                data = result["data"]

                # 如果数据是列表，逐项输出
                if isinstance(data, list):
                    for item in data:
                        self._print_item(item)
                # 如果数据是字典或对象，输出键值对
                else:
                    self._print_item(data)

                # 如果有内容，直接输出
                if isinstance(data, dict) and "content" in data:
                    console.print(data["content"])
        else:
            # 输出错误信息
            error_message = result.get("error", "未知错误")
            console.print(f"[bold red]错误:[/bold red] {error_message}")

    def _print_item(self, item: Any) -> None:
        """
        打印单个项目

        Args:
            item: 要打印的项目
        """
        if hasattr(item, "dict"):
            # 如果对象有dict方法，转换为字典
            item = item.dict()

        if isinstance(item, dict):
            # 如果是字典，格式化输出
            if "id" in item and "name" in item:
                console.print(f"[bold]ID:[/bold] {item['id']}")
                console.print(f"[bold]名称:[/bold] {item['name']}")
                if "type" in item:
                    console.print(f"[bold]类型:[/bold] {item['type']}")
                if "description" in item:
                    desc = item["description"]
                    if len(desc) > 80:
                        desc = desc[:80] + "..."
                    console.print(f"[bold]描述:[/bold] {desc}")
                console.print("-" * 40)
            elif "file_path" in item:
                # 特殊处理文件路径
                console.print(f"[bold]文件路径:[/bold] {item['file_path']}")
                if "content_length" in item:
                    console.print(f"[bold]内容长度:[/bold] {item['content_length']} 字符")
                console.print("-" * 40)
        else:
            # 如果不是字典或对象，直接输出字符串表示
            console.print(str(item))
