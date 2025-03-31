#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Projects 工具集主入口脚本.

提供了一个命令行接口，用于访问GitHub Projects相关的功能：
1. 导入路线图数据到GitHub Projects
2. 从GitHub Projects导出路线图数据
3. 生成可视化的路线图报告

用法:
    python -m scripts.github.projects.main [command] [options]
"""

import argparse
import os
import sys
from typing import Any

import yaml

from .import_roadmap import RoadmapImporter
from .roadmap_generator import RoadmapGenerator
from .roadmap_processor import RoadmapProcessor


def import_roadmap(args: argparse.Namespace) -> None:
    """导入路线图数据到GitHub Projects.

    Args:
        args: 命令行参数
    """
    print("从路线图导入项目数据...")

    importer = RoadmapImporter(owner=args.owner, repo=args.repo, token=args.token)

    try:
        # 加载路线图数据
        data = importer.load_data(args.file)

        # 导入数据到GitHub
        result = importer.import_to_github(data)

        print("\n导入完成:")
        print(f"  项目编号: {result.get('project_number')}")
        print(f"  创建的里程碑: {result.get('milestones')}")
        print(f"  创建的任务: {result.get('issues')}")
    except Exception as e:
        print(f"导入失败: {e}")
        sys.exit(1)


def generate_roadmap(args: argparse.Namespace) -> None:
    """从GitHub Projects生成路线图报告.

    Args:
        args: 命令行参数
    """
    print(f"生成路线图: {args.owner}/{args.repo} -> {args.output_dir}")

    generator = RoadmapGenerator(
        owner=args.owner,
        repo=args.repo,
        project_number=args.project_number,
        output_dir=args.output_dir,
        token=args.token,
    )

    try:
        # 生成路线图
        formats = []
        if args.json:
            formats.append("json")
        if args.markdown:
            formats.append("markdown")
        if args.html:
            formats.append("html")

        if not formats:  # 默认生成所有格式
            formats = ["json", "markdown", "html"]

        results = generator.generate(formats=formats)

        print("\n生成完成:")
        for fmt, path in results.items():
            print(f"  {fmt}: {path}")
    except Exception as e:
        print(f"生成失败: {e}")
        sys.exit(1)


def export_roadmap(args: argparse.Namespace) -> None:
    """从GitHub Projects导出路线图数据.

    Args:
        args: 命令行参数
    """
    print(f"导出路线图: {args.owner}/{args.repo} -> {args.output}")

    processor = RoadmapProcessor()

    try:
        # 获取项目数据
        from ..api import GitHubProjectsClient

        client = GitHubProjectsClient(args.token)
        project_data = client.get_project_v2(
            owner=args.owner, repo=args.repo, project_number=args.project_number
        )

        if not project_data:
            print(f"错误: 无法获取项目数据")
            sys.exit(1)

        # 处理路线图数据
        roadmap_data = processor.process_roadmap_data(project_data)

        # 导出数据
        import json

        output_format = args.format.lower()
        with open(args.output, "w", encoding="utf-8") as f:
            if output_format == "json":
                json.dump(roadmap_data, f, ensure_ascii=False, indent=2)
            elif output_format == "yaml":
                yaml.dump(roadmap_data, f, allow_unicode=True, default_flow_style=False)
            else:
                print(f"错误: 不支持的输出格式 - {output_format}")
                sys.exit(1)

        print(f"\n导出完成: {args.output}")
    except Exception as e:
        print(f"导出失败: {e}")
        sys.exit(1)


def setup_import_parser(subparsers: Any) -> None:
    """设置导入命令的参数解析器.

    Args:
        subparsers: 子命令解析器
    """
    parser = subparsers.add_parser("import", help="导入路线图数据到GitHub Projects")
    parser.add_argument("-f", "--file", required=True, help="路线图数据文件 (YAML或Markdown格式)")
    parser.add_argument("-o", "--owner", required=True, help="GitHub仓库所有者")
    parser.add_argument("-r", "--repo", required=True, help="GitHub仓库名称")
    parser.add_argument("-t", "--token", help="GitHub个人访问令牌 (默认从环境变量GITHUB_TOKEN获取)")
    parser.set_defaults(func=import_roadmap)


def setup_generate_parser(subparsers: Any) -> None:
    """设置生成命令的参数解析器.

    Args:
        subparsers: 子命令解析器
    """
    parser = subparsers.add_parser("generate", help="从GitHub Projects生成路线图报告")
    parser.add_argument("-o", "--owner", required=True, help="GitHub仓库所有者")
    parser.add_argument("-r", "--repo", required=True, help="GitHub仓库名称")
    parser.add_argument("-p", "--project-number", required=True, type=int, help="GitHub项目编号")
    parser.add_argument("-d", "--output-dir", default="./outputs", help="输出目录 (默认: ./outputs)")
    parser.add_argument("--json", action="store_true", help="生成JSON格式输出")
    parser.add_argument("--markdown", action="store_true", help="生成Markdown格式输出")
    parser.add_argument("--html", action="store_true", help="生成HTML格式输出")
    parser.add_argument("-t", "--token", help="GitHub个人访问令牌 (默认从环境变量GITHUB_TOKEN获取)")
    parser.set_defaults(func=generate_roadmap)


def setup_export_parser(subparsers: Any) -> None:
    """设置导出命令的参数解析器.

    Args:
        subparsers: 子命令解析器
    """
    parser = subparsers.add_parser("export", help="从GitHub Projects导出路线图数据")
    parser.add_argument("-o", "--owner", required=True, help="GitHub仓库所有者")
    parser.add_argument("-r", "--repo", required=True, help="GitHub仓库名称")
    parser.add_argument("-p", "--project-number", required=True, type=int, help="GitHub项目编号")
    parser.add_argument("--output", required=True, help="输出文件路径")
    parser.add_argument(
        "--format", choices=["json", "yaml"], default="yaml", help="输出格式 (默认: yaml)"
    )
    parser.add_argument("-t", "--token", help="GitHub个人访问令牌 (默认从环境变量GITHUB_TOKEN获取)")
    parser.set_defaults(func=export_roadmap)


def main() -> None:
    """命令行入口点."""
    parser = argparse.ArgumentParser(description="GitHub Projects 路线图工具集")

    # 设置子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 添加子命令解析器
    setup_import_parser(subparsers)
    setup_generate_parser(subparsers)
    setup_export_parser(subparsers)

    # 解析命令行参数
    args = parser.parse_args()

    # 执行对应的命令
    if hasattr(args, "func"):
        # 如果未提供token，尝试从环境变量获取
        if getattr(args, "token", None) is None:
            args.token = os.environ.get("GITHUB_TOKEN")

        # 执行命令
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
