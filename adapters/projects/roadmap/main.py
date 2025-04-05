#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路线图模块主入口.

提供完整的路线图功能，集成所有子模块。
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

# 确保能够导入上层模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# 导入API客户端
from scripts.github_project.api import GitHubProjectsClient

from .converters import RoadmapConverter
from .data_merger import RoadmapMerger
from .formatters import format_roadmap_data

# 导入核心组件
from .generator import RoadmapGenerator
from .markdown_helper import generate_markdown, parse_markdown_file
from .templates import apply_template, get_roadmap_template
from .validators import validate_roadmap_data


class RoadmapManager:
    """路线图管理器，提供统一的功能接口"""

    def __init__(self, github_client=None, config=None):
        """
        初始化路线图管理器

        Args:
            github_client: GitHub API客户端
            config: 配置信息
        """
        self.github_client = github_client or GitHubProjectsClient()
        self.generator = RoadmapGenerator(github_client, config)
        self.config = config or {}

    def generate_from_github(
        self,
        owner: str,
        repo: str,
        project_number: int,
        template: str = "default",
        output_formats: List[str] = None,
    ) -> Dict[str, str]:
        """
        从GitHub项目生成路线图

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_number: 项目编号
            template: 模板名称
            output_formats: 输出格式列表

        Returns:
            Dict[str, str]: 格式到文件路径的映射
        """
        # 默认输出所有格式
        if output_formats is None:
            output_formats = ["json", "markdown", "html"]

        # 获取项目数据
        project_data = self.github_client.get_project_v2(owner, repo, project_number)
        if not project_data:
            raise ValueError(f"无法获取项目数据: {owner}/{repo} #{project_number}")

        # 生成路线图
        roadmap_data = self.generator.generate_roadmap(project_data)

        # 应用指定模板
        if template != "none":
            template_data = get_roadmap_template(template)
            roadmap_data = apply_template(roadmap_data, template_data)

        # 输出到指定格式
        output_dir = self.config.get("output_dir", "./outputs/roadmap")
        os.makedirs(output_dir, exist_ok=True)

        result = {}
        for fmt in output_formats:
            fmt = fmt.lower()
            if fmt in ["json", "yaml", "markdown", "html"]:
                file_ext = "yml" if fmt == "yaml" else fmt
                if fmt == "html":
                    file_ext = "html"

                output_path = os.path.join(output_dir, f"roadmap.{file_ext}")

                if fmt == "json":
                    RoadmapConverter.to_json(roadmap_data, output_path)
                elif fmt == "yaml":
                    RoadmapConverter.to_yaml(roadmap_data, output_path)
                elif fmt == "markdown":
                    generate_markdown(roadmap_data, output_path)
                elif fmt == "html":
                    html_content = format_roadmap_data(roadmap_data, "html")
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(html_content)

                result[fmt] = output_path

        return result

    def import_from_markdown(
        self, file_paths: List[str], merge_strategy: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        从Markdown文件导入路线图数据

        Args:
            file_paths: Markdown文件路径列表
            merge_strategy: 合并策略

        Returns:
            Dict[str, Any]: 合并后的路线图数据
        """
        roadmaps = []

        for file_path in file_paths:
            try:
                roadmap_data = parse_markdown_file(file_path)
                roadmaps.append(roadmap_data)
            except Exception as e:
                print(f"解析文件 {file_path} 失败: {e}")

        if not roadmaps:
            raise ValueError("没有可用的路线图数据")

        # 如果只有一个文件，直接返回
        if len(roadmaps) == 1:
            return roadmaps[0]

        # 合并多个路线图
        return RoadmapMerger.merge_roadmaps(roadmaps, merge_strategy)

    def export_to_formats(
        self, roadmap_data: Dict[str, Any], formats: List[str], output_dir: str
    ) -> Dict[str, str]:
        """
        将路线图导出为多种格式

        Args:
            roadmap_data: 路线图数据
            formats: 输出格式列表
            output_dir: 输出目录

        Returns:
            Dict[str, str]: 格式到文件路径的映射
        """
        os.makedirs(output_dir, exist_ok=True)

        result = {}
        for fmt in formats:
            fmt = fmt.lower()
            if fmt in ["json", "yaml", "markdown", "html"]:
                file_ext = "yml" if fmt == "yaml" else fmt
                output_path = os.path.join(output_dir, f"roadmap.{file_ext}")

                if fmt == "json":
                    RoadmapConverter.to_json(roadmap_data, output_path)
                elif fmt == "yaml":
                    RoadmapConverter.to_yaml(roadmap_data, output_path)
                elif fmt == "markdown":
                    generate_markdown(roadmap_data, output_path)
                elif fmt == "html":
                    html_content = format_roadmap_data(roadmap_data, "html")
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(html_content)

                result[fmt] = output_path

        return result


def main():
    """命令行入口点"""
    parser = argparse.ArgumentParser(description="路线图生成和管理工具")

    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 从GitHub生成路线图子命令
    github_parser = subparsers.add_parser("github", help="从GitHub项目生成路线图")
    github_parser.add_argument("--owner", required=True, help="仓库所有者")
    github_parser.add_argument("--repo", required=True, help="仓库名称")
    github_parser.add_argument("--project", type=int, required=True, help="项目编号")
    github_parser.add_argument("--output", default="./outputs/roadmap", help="输出目录")
    github_parser.add_argument("--formats", default="json,markdown,html", help="输出格式，逗号分隔")
    github_parser.add_argument("--template", default="default", help="使用的模板")

    # 从Markdown导入子命令
    import_parser = subparsers.add_parser("import", help="从Markdown文件导入路线图")
    import_parser.add_argument("--input", required=True, nargs="+", help="输入文件路径")
    import_parser.add_argument("--output", default="./outputs/roadmap", help="输出目录")
    import_parser.add_argument("--formats", default="json", help="输出格式，逗号分隔")

    # 转换子命令
    convert_parser = subparsers.add_parser("convert", help="转换路线图格式")
    convert_parser.add_argument("--input", required=True, help="输入文件路径")
    convert_parser.add_argument("--output", required=True, help="输出文件路径")
    convert_parser.add_argument(
        "--format", choices=["json", "yaml", "markdown", "html"], required=True, help="输出格式"
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 初始化路线图管理器
    manager = RoadmapManager()

    # 根据子命令执行对应操作
    try:
        if args.command == "github":
            # 从GitHub生成路线图
            output_formats = args.formats.split(",")
            outputs = manager.generate_from_github(
                owner=args.owner,
                repo=args.repo,
                project_number=args.project,
                template=args.template,
                output_formats=output_formats,
            )

            print("\n路线图生成成功:")
            for fmt, path in outputs.items():
                print(f"- {fmt.upper()}: {path}")

        elif args.command == "import":
            # 从Markdown导入
            roadmap_data = manager.import_from_markdown(args.input)

            # 导出到指定格式
            output_formats = args.formats.split(",")
            outputs = manager.export_to_formats(roadmap_data, output_formats, args.output)

            print("\n路线图导入成功:")
            for fmt, path in outputs.items():
                print(f"- {fmt.upper()}: {path}")

        elif args.command == "convert":
            # 读取输入文件
            roadmap_data = RoadmapConverter.from_file(args.input)

            # 转换并输出
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

        else:
            parser.print_help()

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
