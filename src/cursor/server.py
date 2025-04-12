#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VibeCopilot Cursor命令MCP服务器

提供统一的命令处理接口，可以在Cursor IDE中使用
按照MCP服务器标准规范实现，使用src.cursor.command_handler执行命令
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import click
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from rich.console import Console
from rich.logging import RichHandler

from src.cursor.command_handler import get_command_handler

logger = logging.getLogger(__name__)
console = Console()

# 创建服务器实例
server = Server("vibecopilot-server")


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """列出所有可用的工具

    Returns:
        List[types.Tool]: 可用工具列表
    """
    # 获取所有可用命令
    command_handler = get_command_handler()
    commands = command_handler.get_available_commands()

    # 将命令转换为MCP工具格式
    tools = []
    for cmd_name, cmd_info in commands.items():
        tool = types.Tool(
            name=f"vibecopilot.{cmd_name}",
            description=cmd_info.get("description", ""),
            inputSchema={
                "type": "object",
                "required": ["command"],
                "properties": {"command": {"type": "string", "description": f"执行 {cmd_name} 命令"}},
            },
        )
        tools.append(tool)

    # 添加内置工具
    tools.extend(
        [
            types.Tool(name="vibecopilot.list_commands", description="获取所有可用命令列表", inputSchema={"type": "object", "properties": {}}),
            types.Tool(
                name="vibecopilot.get_command_help",
                description="获取命令帮助信息",
                inputSchema={
                    "type": "object",
                    "required": ["command"],
                    "properties": {"command": {"type": "string", "description": "要获取帮助的命令名称"}},
                },
            ),
        ]
    )

    return tools


@server.call_tool()
async def handle_execute_command(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """执行VibeCopilot命令

    Args:
        name: 工具名称
        arguments: 命令参数

    Returns:
        List[types.TextContent]: 命令执行结果
    """
    command = arguments.get("command")
    if not command:
        raise ValueError("缺少必要的command参数")

    # 调用命令处理器执行命令
    command_handler = get_command_handler()
    result = command_handler.handle_command(command)

    # 将结果转换为TextContent格式
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


@server.call_tool()
async def handle_list_commands(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """获取所有可用命令列表

    Args:
        name: 工具名称
        arguments: 命令参数

    Returns:
        List[types.TextContent]: 命令列表
    """
    command_handler = get_command_handler()
    commands = command_handler.get_available_commands()
    result = {"commands": commands, "count": len(commands)}

    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


@server.call_tool()
async def handle_get_command_help(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """获取特定命令的帮助信息

    Args:
        name: 工具名称
        arguments: 命令参数

    Returns:
        List[types.TextContent]: 命令帮助信息
    """
    command = arguments.get("command")
    if not command:
        raise ValueError("缺少必要的command参数")

    help_info = get_command_handler().get_command_help(command)

    return [types.TextContent(type="text", text=json.dumps(help_info, ensure_ascii=False, indent=2))]


def setup_logging(verbose: bool):
    """配置日志系统

    Args:
        verbose: 是否启用详细日志
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[RichHandler(rich_tracebacks=True)])


async def run_server():
    """运行MCP服务器"""
    # 使用stdio运行服务器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="vibecopilot-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


@click.command()
@click.option(
    "--workspace",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="工作目录路径，默认为当前目录",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="启用详细日志输出",
)
def main(workspace: Optional[str], verbose: bool):
    """VibeCopilot MCP命令服务器 (stdio)

    启动符合MCP规范的命令服务器，使用stdio与Cursor IDE通信。
    服务器将处理VibeCopilot命令并通过src.cursor.command_handler执行。
    """
    setup_logging(verbose)

    # 显示服务器信息
    console.print("[bold blue]====================================[/bold blue]")
    console.print("[bold green]VibeCopilot MCP命令服务器[/bold green]")
    console.print("[bold blue]====================================[/bold blue]")

    if workspace:
        os.chdir(workspace)
        console.print(f"[blue]工作目录:[/blue] {workspace}")
    else:
        console.print(f"[blue]工作目录:[/blue] {os.getcwd()} (当前目录)")

    console.print(f"[blue]Python版本:[/blue] {sys.version.split()[0]}")
    console.print(f"[blue]日志级别:[/blue] {'DEBUG' if verbose else 'INFO'}")
    console.print("[bold blue]====================================[/bold blue]")

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        console.print("\n[yellow]收到中断信号，服务器已停止[/yellow]")
    except Exception as e:
        console.print(f"[bold red]服务器启动失败: {str(e)}[/bold red]")
        logger.error("服务器启动失败", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
