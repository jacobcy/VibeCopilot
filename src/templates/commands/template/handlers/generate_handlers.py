"""
模板生成和渲染命令处理模块

提供模板的生成、渲染和执行功能
"""

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console

from src.db import get_session_factory
from src.templates.core.template_manager import TemplateManager
from src.templates.generators import LLMGenerationConfig, LLMTemplateGenerator, RegexTemplateGenerator

logger = logging.getLogger(__name__)
console = Console()


def handle_template_generate(args: argparse.Namespace) -> None:
    """
    处理模板生成命令

    Args:
        args: 命令行参数
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        # 创建模板管理器
        template_manager = TemplateManager(session)

        # 检查输入类型
        input_content = None
        input_type = "text"

        if hasattr(args, "input") and args.input:
            # 从文件读取输入内容
            input_path = Path(args.input)
            if not input_path.exists():
                console.print(f"[bold red]错误: 输入文件 {input_path} 不存在[/bold red]")
                return

            input_content = input_path.read_text(encoding="utf-8")
            input_type = "file"

        elif hasattr(args, "text") and args.text:
            # 直接使用文本输入
            input_content = args.text
            input_type = "text"

        elif hasattr(args, "prompt") and args.prompt:
            # 使用提示输入
            input_content = args.prompt
            input_type = "prompt"

        else:
            console.print("[bold red]错误: 必须提供输入内容（--input, --text 或 --prompt）[/bold red]")
            return

        # 解析生成器类型
        generator_type = args.generator if hasattr(args, "generator") else "regex"

        # 配置生成器
        if generator_type == "llm":
            # 配置LLM生成器
            llm_config = LLMGenerationConfig(
                model=args.model if hasattr(args, "model") and args.model else "gpt-3.5-turbo",
                temperature=args.temperature if hasattr(args, "temperature") else 0.7,
                max_tokens=args.max_tokens if hasattr(args, "max_tokens") else 2000,
            )

            # 创建生成器
            generator = LLMTemplateGenerator(llm_config)
        else:
            # 默认使用正则生成器
            generator = RegexTemplateGenerator()

        # 解析输出路径
        output_path = args.output if hasattr(args, "output") else None

        # 解析模板类型
        template_type = args.type if hasattr(args, "type") else "generic"

        # 解析模板名称
        template_name = args.name if hasattr(args, "name") else f"Generated {template_type.capitalize()} Template"

        # 生成模板
        if generator_type == "llm":
            # LLM生成需要提示
            prompt_prefix = args.prefix if hasattr(args, "prefix") else ""
            prompt_suffix = args.suffix if hasattr(args, "suffix") else ""

            template_result = generator.generate(input_content, template_type=template_type, prompt_prefix=prompt_prefix, prompt_suffix=prompt_suffix)
        else:
            # 正则表达式生成
            template_result = generator.generate(input_content, template_type=template_type)

        # 处理生成结果
        if not template_result or not template_result.content:
            console.print("[bold red]错误: 无法生成模板内容[/bold red]")
            return

        # 保存模板
        if args.save:
            # 添加或更新元数据
            if not template_result.metadata:
                from src.models.template import TemplateMetadata

                template_result.metadata = TemplateMetadata(author="模板生成器", version="1.0.0", tags=[template_type, "自动生成"])

            # 更新名称
            template_result.name = template_name

            # 保存到数据库
            result = template_manager.add_template(template_result)
            console.print(f"[bold green]模板已保存到数据库: {result.id}[/bold green]")

        # 输出模板内容
        if output_path:
            # 写入文件
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(template_result.content, encoding="utf-8")
            console.print(f"[bold green]模板内容已写入文件: {output_path}[/bold green]")
        else:
            # 直接显示
            console.print("[bold]生成的模板内容:[/bold]")
            console.print(template_result.content)

    finally:
        session.close()


def handle_template_render(args: argparse.Namespace) -> None:
    """
    处理模板渲染命令

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

        # 获取变量值
        variables = {}

        # 从命令行参数获取
        if hasattr(args, "var") and args.var:
            for var in args.var:
                if "=" in var:
                    key, value = var.split("=", 1)
                    variables[key] = value

        # 从JSON文件获取
        if hasattr(args, "vars_file") and args.vars_file:
            vars_path = Path(args.vars_file)
            if not vars_path.exists():
                console.print(f"[bold red]错误: 变量文件 {vars_path} 不存在[/bold red]")
                return

            try:
                with open(vars_path, "r", encoding="utf-8") as f:
                    file_vars = json.load(f)
                    if isinstance(file_vars, dict):
                        variables.update(file_vars)
                    else:
                        console.print("[bold red]错误: 变量文件必须包含JSON对象[/bold red]")
                        return
            except json.JSONDecodeError:
                console.print("[bold red]错误: 变量文件必须是有效的JSON[/bold red]")
                return

        # 检查是否缺少必要变量
        missing_vars = []
        if template.variables:
            for var in template.variables:
                if getattr(var, "required", True) and var.name not in variables and not hasattr(var, "default"):
                    missing_vars.append(var.name)

        if missing_vars:
            console.print(f"[bold red]错误: 缺少必要变量: {', '.join(missing_vars)}[/bold red]")
            return

        # 渲染模板
        result = template_manager.render_template(template_id, variables)

        # 输出渲染结果
        if hasattr(args, "output") and args.output:
            # 写入文件
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result, encoding="utf-8")
            console.print(f"[bold green]渲染结果已写入文件: {args.output}[/bold green]")
        else:
            # 直接显示
            console.print("[bold]渲染结果:[/bold]")
            console.print(result)

    finally:
        session.close()
