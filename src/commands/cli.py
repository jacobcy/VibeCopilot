#!/usr/bin/env python3
"""
VibeCopilot - CLI命令模块

定义命令行接口
"""

import logging
import sys
from typing import Optional

import typer
from rich.console import Console

from src import __version__
from src.commands.handlers import (
    handle_advance_command,
    handle_document_command,
    handle_init_command,
    handle_status_command,
    handle_task_command,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建Typer应用
app = typer.Typer(
    name="vibecopilot",
    help="AI-powered development workflow assistant",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print the version of the package."""
    if value:
        console.print(f"[bold]VibeCopilot[/bold] version: " f"[bold blue]{__version__}[/bold blue]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application version and exit.",
        callback=version_callback,
        is_eager=True,
    )
) -> None:
    """
    VibeCopilot - AI辅助项目管理工具
    """
    pass


@app.command()
def init(
    project_name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Name of the project to initialize.",
    ),
    directory: str = typer.Option(
        ".",
        "--directory",
        "-d",
        help="Directory to initialize the project in.",
    ),
) -> None:
    """
    初始化新项目
    """
    handle_init_command(project_name, directory)


@app.command()
def status(
    path: str = typer.Option(
        ".",
        "--path",
        "-p",
        help="Path to the project.",
    )
) -> None:
    """
    显示项目状态
    """
    handle_status_command(path)


@app.command()
def task(
    phase: str = typer.Option(..., "--phase", "-ph", help="项目阶段名称"),
    task_id: str = typer.Option(..., "--task", "-t", help="任务ID"),
    status: str = typer.Option(..., "--status", "-s", help="任务状态"),
    progress: Optional[int] = typer.Option(None, "--progress", "-pr", help="任务进度百分比"),
    path: str = typer.Option(".", "--path", "-p", help="项目路径"),
) -> None:
    """
    更新任务状态
    """
    handle_task_command(phase, task_id, status, progress, path)


@app.command()
def advance(
    path: str = typer.Option(".", "--path", "-p", help="项目路径"),
) -> None:
    """
    推进到下一个项目阶段
    """
    handle_advance_command(path)


@app.command()
def document(
    doc_type: str = typer.Option(..., "--type", "-t", help="文档类型"),
    status: str = typer.Option(..., "--status", "-s", help="文档状态"),
    path: str = typer.Option(".", "--path", "-p", help="项目路径"),
) -> None:
    """
    更新文档状态
    """
    handle_document_command(doc_type, status, path)


def run_cli() -> None:
    """运行CLI应用"""
    app()
