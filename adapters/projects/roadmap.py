#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路线图模块兼容层.

提供向后兼容的接口，支持旧的调用方式。
"""

import os
import sys
from typing import Any, Dict, List, Optional

# 确保能够导入上层模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from scripts.github_project.api import GitHubProjectsClient

# 导入新的路线图模块
from scripts.github_project.projects.roadmap.generator import RoadmapGenerator
from scripts.github_project.projects.roadmap.main import RoadmapManager


class RoadmapGeneratorLegacy:
    """
    路线图生成器的兼容类.

    提供与原始RoadmapGenerator相同的接口，但使用新的模块化实现。
    """

    def __init__(
        self,
        owner: str,
        repo: str,
        project_number: int,
        output_dir: str = "./outputs",
        token: Optional[str] = None,
    ) -> None:
        """初始化路线图生成器.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            project_number: 项目编号
            output_dir: 输出目录
            token: GitHub访问令牌，如果未提供则从环境变量中获取
        """
        self.owner = owner
        self.repo = repo
        self.project_number = project_number
        self.output_dir = output_dir
        self.token = token

        # 初始化新的客户端和管理器
        self.client = GitHubProjectsClient(token)
        self.manager = RoadmapManager(self.client, {"output_dir": output_dir})

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, formats: List[str] = []) -> Dict[str, str]:
        """生成路线图.

        Args:
            formats: 输出格式列表，可选值: "json", "markdown", "html"

        Returns:
            Dict[str, str]: 格式到文件路径的映射
        """
        # 默认生成所有格式
        if not formats:
            formats = ["json", "markdown", "html"]

        # 使用新的实现生成路线图
        return self.manager.generate_from_github(
            owner=self.owner,
            repo=self.repo,
            project_number=self.project_number,
            output_formats=formats,
        )

    def _generate_json(self, data: Dict) -> str:
        """生成JSON格式的路线图.

        Args:
            data: 路线图数据

        Returns:
            str: 生成的文件路径
        """
        from scripts.github_project.projects.roadmap.converters import RoadmapConverter

        file_path = os.path.join(self.output_dir, "roadmap.json")
        RoadmapConverter.to_json(data, file_path)
        return file_path

    def _generate_markdown(self, data: Dict) -> str:
        """生成Markdown格式的路线图.

        Args:
            data: 路线图数据

        Returns:
            str: 生成的文件路径
        """
        from scripts.github_project.projects.roadmap.markdown_helper import generate_markdown

        file_path = os.path.join(self.output_dir, "roadmap.md")
        generate_markdown(data, file_path)
        return file_path

    def _generate_html(self, data: Dict) -> str:
        """生成HTML格式的路线图.

        Args:
            data: 路线图数据

        Returns:
            str: 生成的文件路径
        """
        from scripts.github_project.projects.roadmap.formatters import format_roadmap_data

        file_path = os.path.join(self.output_dir, "roadmap.html")
        html_content = format_roadmap_data(data, "html")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return file_path

    def process_milestone_data(self, data):
        """处理里程碑数据.

        向后兼容的方法，但实际使用新的实现。
        """
        from scripts.github_project.projects.roadmap_processor import RoadmapProcessor

        processor = RoadmapProcessor()
        return processor.process_roadmap_data(data)

    def _generate_phase_list(self):
        """生成阶段列表.

        向后兼容的方法，但实际使用新的实现。
        """
        # 这个方法在新的实现中不再需要，但为了兼容性保留
        pass

    def format_milestone_data(self, milestone_node):
        """格式化里程碑数据.

        向后兼容的方法，但实际使用新的实现。
        """
        # 这个方法在新的实现中不再需要，但为了兼容性保留
        due_date = None
        if milestone_node["dueOn"]:
            iso_date = milestone_node["dueOn"].replace("Z", "+00:00")
            due_date = datetime.fromisoformat(iso_date)

        return {
            "id": milestone_node["id"],
            "title": milestone_node["title"],
            "description": milestone_node["description"] or "",
            "due_date": due_date,
            "number": milestone_node["number"],
        }


# 为了向后兼容，将旧的类暴露为默认名称
RoadmapGenerator = RoadmapGeneratorLegacy


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="生成项目路线图")
    parser.add_argument("--owner", required=True, help="仓库所有者")
    parser.add_argument("--repo", required=True, help="仓库名称")
    parser.add_argument("--project", type=int, required=True, help="项目编号")
    parser.add_argument("--output", default="docs/roadmap", help="输出目录")
    parser.add_argument("--formats", default="md,html,json", help="输出格式，逗号分隔")

    args = parser.parse_args()

    # 创建路线图生成器
    generator = RoadmapGenerator(
        owner=args.owner,
        repo=args.repo,
        project_number=args.project,
        output_dir=args.output,
    )

    # 生成路线图
    formats = args.formats.split(",")
    outputs = generator.generate(formats)

    # 输出结果
    if outputs:
        print("路线图生成成功:")
        for fmt, path in outputs.items():
            print(f"- {fmt.upper()}: {path}")
    else:
        print("路线图生成失败")
