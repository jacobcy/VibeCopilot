"""
模板编辑命令处理模块

提供模板的创建、导入和更新功能
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

from rich.console import Console

from src.db import get_session_factory
from src.models.template import Template, TemplateMetadata
from src.templates.core.template_manager import TemplateManager

logger = logging.getLogger(__name__)
console = Console()


def handle_template_import(args: argparse.Namespace) -> None:
    """
    处理模板导入命令

    Args:
        args: 命令行参数
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 检查文件是否存在
        file_path = Path(args.file_path)
        if not file_path.exists():
            console.print(f"[bold red]错误: 文件 {file_path} 不存在[/bold red]")
            return

        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 导入模板
        template = template_manager.import_template_from_file(file_path, args.overwrite)
        if not template:
            console.print(f"[bold red]错误: 导入模板失败[/bold red]")
            return

        console.print(f"[bold green]成功导入模板: {template.id}[/bold green]")

    finally:
        session.close()


def handle_template_create(args: argparse.Namespace) -> None:
    """
    处理模板创建命令

    Args:
        args: 命令行参数
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 检查内容来源
        content = ""
        if args.content:
            content = args.content
        elif args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                console.print(f"[bold red]错误: 文件 {file_path} 不存在[/bold red]")
                return
            content = file_path.read_text(encoding="utf-8")
        else:
            console.print("[bold red]错误: 必须提供内容或内容文件[/bold red]")
            return

        # 创建模板对象
        template = Template(
            id=None,  # 自动生成
            name=args.name,
            type=args.type,
            description=args.description or "",
            content=content,
            metadata=TemplateMetadata(author="命令行创建", tags=[], version="1.0.0"),
        )

        # 添加模板
        result = template_manager.add_template(template)

        console.print(f"[bold green]成功创建模板: {result.id}[/bold green]")

    finally:
        session.close()


def handle_template_update(args: argparse.Namespace) -> None:
    """
    处理模板更新命令

    Args:
        args: 命令行参数
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 获取模板ID
        template_id = args.template_id

        # 检查模板是否存在
        template = template_manager.get_template(template_id)
        if not template:
            console.print(f"[bold red]错误: 模板 {template_id} 不存在[/bold red]")
            return

        # 准备更新数据
        update_data = {}

        # 名称
        if hasattr(args, "name") and args.name:
            update_data["name"] = args.name

        # 描述
        if hasattr(args, "description") and args.description:
            update_data["description"] = args.description

        # 类型
        if hasattr(args, "type") and args.type:
            update_data["type"] = args.type

        # 内容
        if hasattr(args, "content") and args.content:
            update_data["content"] = args.content
        elif hasattr(args, "file") and args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                console.print(f"[bold red]错误: 文件 {file_path} 不存在[/bold red]")
                return
            update_data["content"] = file_path.read_text(encoding="utf-8")

        # 标签
        if hasattr(args, "tags") and args.tags:
            # 如果模板没有元数据，创建一个
            if not template.metadata:
                template.metadata = TemplateMetadata(author="命令行更新", version="1.0.0", tags=[])
                update_data["metadata"] = template.metadata.dict()

            # 更新标签
            update_data.setdefault("metadata", {})["tags"] = args.tags.split(",")

        # 更新模板
        if update_data:
            result = template_manager.update_template(template_id, update_data)
            if result:
                console.print(f"[bold green]成功更新模板: {template_id}[/bold green]")
            else:
                console.print(f"[bold red]更新模板失败: {template_id}[/bold red]")
        else:
            console.print("[bold yellow]警告: 未提供任何更新数据[/bold yellow]")

    finally:
        session.close()


def handle_template_load(args: argparse.Namespace) -> None:
    """
    处理模板加载命令（从目录加载多个模板）

    Args:
        args: 命令行参数
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 获取目录路径
        directory = args.directory
        if not Path(directory).exists() or not Path(directory).is_dir():
            console.print(f"[bold red]错误: 目录 {directory} 不存在或不是一个目录[/bold red]")
            return

        # 获取模板类型
        template_type = args.type if hasattr(args, "type") else None

        # 递归参数
        recursive = args.recursive if hasattr(args, "recursive") else False

        # 加载模板
        results = template_manager.load_templates_from_directory(
            directory, template_type=template_type, recursive=recursive, overwrite=args.overwrite
        )

        # 输出结果
        console.print(f"[bold green]成功加载 {len(results)} 个模板[/bold green]")
        for result in results:
            console.print(f"  - {result.id}: {result.name}")

    finally:
        session.close()
