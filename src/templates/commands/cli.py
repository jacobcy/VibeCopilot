#!/usr/bin/env python3
"""
VibeCopilot - CLI命令模块

定义命令行接口
"""

import argparse
import logging
import sys
from typing import List, Optional

import typer
from rich.console import Console

from src import __version__
from src.commands.handlers import (
    handle_advance_command,
    handle_document_command,
    handle_init_command,
    handle_status_command,
    handle_task_command,
    handle_template_command,
)

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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


@app.command()
def template(
    subcommand: str = typer.Argument(..., help="子命令: list, show, generate, import, load等"),
    template_id: Optional[str] = typer.Option(None, "--id", "-i", help="模板ID"),
    template_type: Optional[str] = typer.Option(None, "--type", "-t", help="模板类型"),
    format: str = typer.Option("table", "--format", "-f", help="输出格式"),
    file_path: Optional[str] = typer.Option(None, "--file", help="模板文件路径"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    variables: Optional[str] = typer.Option(None, "--vars", "-v", help="变量JSON字符串"),
    variables_file: Optional[str] = typer.Option(None, "--vars-file", help="变量文件路径"),
    templates_dir: Optional[str] = typer.Option(None, "--dir", "-d", help="模板目录"),
    overwrite: bool = typer.Option(False, "--overwrite", help="覆盖已有模板"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="标签过滤"),
) -> None:
    """
    模板管理和生成
    """
    args = argparse.Namespace(
        subcommand=subcommand,
        template_id=template_id,
        template_type=template_type,
        format=format,
        file_path=file_path,
        output=output,
        variables=variables,
        variables_file=variables_file,
        templates_dir=templates_dir,
        overwrite=overwrite,
        tags=tags,
    )
    handle_template_command(args)


def run_cli() -> None:
    """运行CLI应用"""
    app()
