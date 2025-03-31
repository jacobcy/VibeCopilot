#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路线图生成器模块.

此模块提供从GitHub Projects生成Markdown和HTML格式路线图视图的功能。
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from ..api import GitHubProjectsClient
from .roadmap_processor import RoadmapProcessor


class RoadmapGenerator:
    """路线图生成器类."""

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

        self.client = GitHubProjectsClient(token)
        self.processor = RoadmapProcessor()

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

        # 获取项目数据
        project_data = self.client.get_project_v2(self.owner, self.repo, self.project_number)

        if not project_data:
            raise ValueError(f"无法获取项目数据: {self.owner}/{self.repo} #{self.project_number}")

        # 处理路线图数据
        roadmap_data = self.processor.process_roadmap_data(project_data)

        # 生成指定格式的路线图
        result = {}

        for fmt in formats:
            if fmt == "json":
                path = self._generate_json(roadmap_data)
                result["json"] = path
            elif fmt == "markdown":
                path = self._generate_markdown(roadmap_data)
                result["markdown"] = path
            elif fmt == "html":
                path = self._generate_html(roadmap_data)
                result["html"] = path
            else:
                print(f"警告: 不支持的格式 - {fmt}")

        return result

    def _generate_json(self, data: Dict) -> str:
        """生成JSON格式的路线图.

        Args:
            data: 路线图数据

        Returns:
            str: 生成的文件路径
        """
        file_path = os.path.join(self.output_dir, "roadmap.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return file_path

    def _generate_markdown(self, data: Dict) -> str:
        """生成Markdown格式的路线图.

        Args:
            data: 路线图数据

        Returns:
            str: 生成的文件路径
        """
        file_path = os.path.join(self.output_dir, "roadmap.md")

        title = data.get("title", "项目路线图")
        description = data.get("description", "")
        milestones = data.get("milestones", [])

        with open(file_path, "w", encoding="utf-8") as f:
            # 写入标题和描述
            f.write(f"# {title}\n\n")

            if description:
                f.write(f"{description}\n\n")

            # 写入里程碑和任务
            for milestone in milestones:
                milestone_name = milestone.get("name", "")
                milestone_description = milestone.get("description", "")
                milestone_status = milestone.get("status", "")
                start_date = milestone.get("start_date", "")
                end_date = milestone.get("end_date", "")

                # 格式化日期
                date_range = ""
                if start_date and end_date:
                    date_range = f" ({start_date} ~ {end_date})"

                # 状态图标
                status_icon = "🏁"
                if milestone_status == "completed":
                    status_icon = "✅"
                elif milestone_status == "in_progress":
                    status_icon = "🟢"

                f.write(f"## {status_icon} {milestone_name}{date_range}\n\n")

                if milestone_description:
                    f.write(f"{milestone_description}\n\n")

                # 写入任务
                tasks = milestone.get("tasks", [])
                for task in tasks:
                    task_title = task.get("title", "")
                    task_status = task.get("status", "")

                    # 状态图标
                    task_icon = ""
                    if task_status == "completed":
                        task_icon = "✅ "
                    elif task_status == "in_progress":
                        task_icon = "🟢 "

                    # 状态标签
                    status_label = ""
                    if task_status == "in_progress":
                        status_label = " `进行中`"

                    f.write(f"- {task_icon}{task_title}{status_label}\n")

                f.write("\n")

        return file_path

    def _generate_html(self, data: Dict) -> str:
        """生成HTML格式的路线图.

        Args:
            data: 路线图数据

        Returns:
            str: 生成的文件路径
        """
        file_path = os.path.join(self.output_dir, "roadmap.html")

        title = data.get("title", "项目路线图")
        description = data.get("description", "")
        milestones = data.get("milestones", [])

        with open(file_path, "w", encoding="utf-8") as f:
            # 写入HTML头部
            f.write(
                f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 30px;
            color: #0366d6;
        }}
        .roadmap-description {{
            text-align: center;
            margin-bottom: 40px;
            font-size: 18px;
            color: #666;
        }}
        .milestone {{
            margin-bottom: 40px;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .milestone-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        .milestone-title {{
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }}
        .milestone-dates {{
            font-size: 14px;
            color: #666;
        }}
        .milestone-description {{
            color: #666;
            margin-bottom: 15px;
        }}
        .tasks {{
            list-style-type: none;
            padding: 0;
        }}
        .task {{
            padding: 10px 15px;
            margin-bottom: 8px;
            border-radius: 4px;
            background-color: #f8f9fa;
            display: flex;
            align-items: center;
        }}
        .task-status {{
            margin-right: 10px;
            font-size: 18px;
        }}
        .status-indicator {{
            display: inline-block;
            padding: 2px 6px;
            font-size: 12px;
            border-radius: 3px;
            margin-left: 8px;
            font-weight: normal;
        }}
        .status-completed {{
            background-color: #dcffe4;
            color: #28a745;
        }}
        .status-in-progress {{
            background-color: #fff8c5;
            color: #735c0f;
        }}
        .status-planned {{
            background-color: #f1f8ff;
            color: #0366d6;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="roadmap-description">{description}</div>
    <div class="roadmap">
"""
            )

            # 写入里程碑和任务
            for milestone in milestones:
                milestone_name = milestone.get("name", "")
                milestone_description = milestone.get("description", "")
                milestone_status = milestone.get("status", "")
                start_date = milestone.get("start_date", "")
                end_date = milestone.get("end_date", "")

                # 格式化日期
                date_range = ""
                if start_date and end_date:
                    date_range = f"{start_date} - {end_date}"

                # 状态图标
                status_icon = "🏁"
                if milestone_status == "completed":
                    status_icon = "✅"
                elif milestone_status == "in_progress":
                    status_icon = "🟢"

                f.write(
                    f"""        <div class="milestone">
            <div class="milestone-header">
                <h2 class="milestone-title">{status_icon} {milestone_name}</h2>
                <div class="milestone-dates">{date_range}</div>
            </div>
"""
                )

                if milestone_description:
                    f.write(
                        f"""            <div class="milestone-description">{milestone_description}</div>\n"""
                    )

                f.write("""            <ul class="tasks">\n""")

                # 写入任务
                tasks = milestone.get("tasks", [])
                for task in tasks:
                    task_title = task.get("title", "")
                    task_status = task.get("status", "")

                    # 状态图标
                    task_icon = "📋"
                    status_class = "status-planned"
                    status_text = "已计划"

                    if task_status == "completed":
                        task_icon = "✅"
                        status_class = "status-completed"
                        status_text = "已完成"
                    elif task_status == "in_progress":
                        task_icon = "🟢"
                        status_class = "status-in-progress"
                        status_text = "进行中"

                    f.write(
                        f"""                <li class="task">
                    <span class="task-status">{task_icon}</span>
                    <span class="task-title">{task_title}</span>
                    <span class="status-indicator {status_class}">{status_text}</span>
                </li>\n"""
                    )

                f.write(
                    """            </ul>
        </div>\n"""
                )

            # 写入HTML尾部
            f.write(
                """    </div>
</body>
</html>"""
            )

        return file_path

    def process_milestone_data(self, data):
        """处理里程碑数据."""
        # 拆分长行
        self.milestones_data = {}

        for m in data["repository"]["milestones"]["edges"]:
            node = m["node"]
            due_date = None

            if node["dueOn"]:
                iso_date = node["dueOn"].replace("Z", "+00:00")
                due_date = datetime.fromisoformat(iso_date)

            self.milestones_data[node["title"]] = {
                "id": node["id"],
                "title": node["title"],
                "description": node["description"] or "",
                "due_date": due_date,
                "number": node["number"],
            }

    def _generate_phase_list(self):
        """生成阶段列表."""
        for phase in self.phases:
            # 添加阶段中的每个任务
            phase_tasks = [
                task for task in self.tasks
                if task.get("phase") == phase["title"]
            ]
            phase["tasks"] = phase_tasks

    def format_milestone_data(self, milestone_node):
        """格式化里程碑数据."""
        due_date = None
        if milestone_node["dueOn"]:
            # 拆分长行
            iso_date = milestone_node["dueOn"].replace("Z", "+00:00")
            due_date = datetime.fromisoformat(iso_date)

        return {
            "id": milestone_node["id"],
            "title": milestone_node["title"],
            "description": milestone_node["description"] or "",
            "due_date": due_date,
            "number": milestone_node["number"],
        }


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
