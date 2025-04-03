#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路线图命令行工具.

提供命令行界面用于生成和管理路线图。
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from scripts.github_project.api import GitHubProjectsClient

from .converters import RoadmapConverter
from .formatters import format_roadmap_data
from .generator import RoadmapGenerator
from .markdown_helper import generate_markdown, parse_markdown_file
from .templates import apply_template, get_roadmap_template


def main():
    """路线图命令行工具入口点."""
    parser = argparse.ArgumentParser(description="路线图生成和管理工具")

    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 生成路线图子命令
    generate_parser = subparsers.add_parser("generate", help="从GitHub Projects生成路线图")
    generate_parser.add_argument("--owner", required=True, help="仓库所有者")
    generate_parser.add_argument("--repo", required=True, help="仓库名称")
    generate_parser.add_argument("--project", type=int, required=True, help="项目编号")
    generate_parser.add_argument("--output", default="./outputs", help="输出目录")
    generate_parser.add_argument("--formats", default="json,markdown,html", help="输出格式，逗号分隔")
    generate_parser.add_argument("--template", default="default", help="使用的模板")

    # 转换路线图子命令
    convert_parser = subparsers.add_parser("convert", help="转换路线图文件格式")
    convert_parser.add_argument("--input", required=True, help="输入文件路径")
    convert_parser.add_argument("--output", required=True, help="输出文件路径")
    convert_parser.add_argument(
        "--format", choices=["json", "yaml", "markdown", "html"], required=True, help="输出格式"
    )

    # 验证路线图子命令
    validate_parser = subparsers.add_parser("validate", help="验证路线图文件")
    validate_parser.add_argument("--input", required=True, help="输入文件路径")

    # 解析命令行参数
    args = parser.parse_args()

    # 根据子命令执行对应操作
    if args.command == "generate":
        generate_roadmap(args)
    elif args.command == "convert":
        convert_roadmap(args)
    elif args.command == "validate":
        validate_roadmap(args)
    else:
        parser.print_help()


def generate_roadmap(args):
    """生成路线图."""
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)

    # 初始化客户端和生成器
    client = GitHubProjectsClient()
    generator = RoadmapGenerator()

    try:
        # 获取项目数据
        print(f"正在获取 {args.owner}/{args.repo} 项目 #{args.project} 的数据...")
        project_data = client.get_project_v2(args.owner, args.repo, args.project)

        if not project_data:
            print(f"错误: 无法获取项目数据")
            return

        # 生成路线图
        print("正在生成路线图...")
        roadmap_data = generator.generate_roadmap(project_data)

        # 应用模板
        if args.template != "none":
            print(f"正在应用模板: {args.template}")
            template = get_roadmap_template(args.template)
            roadmap_data = apply_template(roadmap_data, template)

        # 输出到不同格式
        formats = args.formats.split(",")
        outputs = {}

        for fmt in formats:
            fmt = fmt.strip().lower()
            if fmt in ["json", "yaml", "markdown", "html"]:
                output_path = os.path.join(
                    args.output, f"roadmap.{fmt if fmt != 'yaml' else 'yml'}"
                )
                print(f"正在生成{fmt.upper()}格式...")

                if fmt == "json":
                    content = RoadmapConverter.to_json(roadmap_data, output_path)
                    outputs["json"] = output_path
                elif fmt == "yaml":
                    content = RoadmapConverter.to_yaml(roadmap_data, output_path)
                    outputs["yaml"] = output_path
                elif fmt == "markdown":
                    content = generate_markdown(roadmap_data, output_path)
                    outputs["markdown"] = output_path
                elif fmt == "html":
                    content = format_roadmap_data(roadmap_data, "html")
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    outputs["html"] = output_path
            else:
                print(f"警告: 不支持的格式 - {fmt}")

        # 输出结果
        if outputs:
            print("\n路线图生成成功:")
            for fmt, path in outputs.items():
                print(f"- {fmt.upper()}: {path}")
        else:
            print("\n没有生成任何输出文件")

    except Exception as e:
        print(f"错误: {e}")


def convert_roadmap(args):
    """转换路线图格式."""
    try:
        print(f"正在读取输入文件: {args.input}")

        # 根据文件扩展名确定输入格式
        _, ext = os.path.splitext(args.input)

        # 读取输入文件
        roadmap_data = RoadmapConverter.from_file(args.input)

        # 转换并输出
        print(f"正在转换为{args.format.upper()}格式...")

        if args.format == "json":
            RoadmapConverter.to_json(roadmap_data, args.output)
        elif args.format == "yaml":
            RoadmapConverter.to_yaml(roadmap_data, args.output)
        elif args.format == "markdown":
            generate_markdown(roadmap_data, args.output)
        elif args.format == "html":
            html_content = format_roadmap_data(roadmap_data, "html")
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(html_content)

        print(f"转换成功，已保存到: {args.output}")

    except Exception as e:
        print(f"转换失败: {e}")


def validate_roadmap(args):
    """验证路线图文件."""
    try:
        print(f"正在验证文件: {args.input}")

        # 读取输入文件
        roadmap_data = RoadmapConverter.from_file(args.input)

        # 导入验证函数
        from .validators import validate_roadmap_data

        # 执行验证
        is_valid = validate_roadmap_data(roadmap_data)

        if is_valid:
            print("验证成功: 路线图数据有效")
            return True
        else:
            print("验证失败: 路线图数据无效")
            return False

    except Exception as e:
        print(f"验证失败: {e}")
        return False


if __name__ == "__main__":
    main()
