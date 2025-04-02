#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路线图导入工具模块.

此脚本读取本地Markdown或YAML格式的路线图数据，
并将其导入到GitHub Projects中，创建对应的milestone、issues和项目视图。
"""

import argparse
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import yaml

from ..api import GitHubIssuesClient, GitHubProjectsClient


class RoadmapImporter:
    """路线图导入工具类."""

    def __init__(self, owner: str, repo: str, token: Optional[str] = None) -> None:
        """初始化路线图导入工具.

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            token: GitHub个人访问令牌，如果未提供，将从环境变量获取
        """
        self.owner = owner
        self.repo = repo
        self.token = token

        # 初始化API客户端
        self.issues_client = GitHubIssuesClient(token)
        self.projects_client = GitHubProjectsClient(token)

        # 存储创建的对象ID映射
        self.milestone_map: Dict[str, int] = {}  # 里程碑ID到编号的映射
        self.issue_map: Dict[str, Dict[str, Any]] = {}  # 任务ID到Issue的映射
        self.field_map: Dict[str, str] = {}  # 字段名到ID的映射

    def load_data(self, file_path: str) -> Dict[str, Any]:
        """加载路线图数据.

        支持YAML和Markdown格式，自动根据文件扩展名判断。

        Args:
            file_path: 数据文件路径

        Returns:
            Dict[str, Any]: 路线图数据
        """
        if not os.path.exists(file_path):
            print(f"错误: 文件不存在 - {file_path}")
            sys.exit(1)

        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            if file_ext in [".yaml", ".yml"]:
                return self._load_yaml(file_path)
            elif file_ext in [".md", ".markdown"]:
                return self._load_markdown(file_path)
            else:
                print(f"错误: 不支持的文件格式 - {file_ext}")
                sys.exit(1)
        except Exception as e:
            print(f"错误: 无法加载路线图数据 - {e}")
            sys.exit(1)

    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """加载YAML格式的路线图数据.

        Args:
            file_path: YAML文件路径

        Returns:
            Dict[str, Any]: 路线图数据
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data

    def _load_markdown(self, file_path: str) -> Dict[str, Any]:
        """加载Markdown格式的路线图数据并转换为结构化数据.

        Args:
            file_path: Markdown文件路径

        Returns:
            Dict[str, Any]: 路线图数据
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析标题和描述
        title = "项目路线图"
        description = ""
        lines = content.split("\n")

        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
            lines = lines[1:]

        # 寻找描述段落（第一个非空行直到第一个二级标题）
        desc_lines = []
        for line in lines:
            if line.startswith("## "):
                break
            if line.strip() and not line.startswith("# "):
                desc_lines.append(line)

        if desc_lines:
            description = "\n".join(desc_lines).strip()

        # 解析里程碑和任务
        milestones = []
        current_milestone = None

        for line in lines:
            line = line.strip()

            # 忽略空行和不相关内容
            if not line or line.startswith("[") or line.startswith("*") or line.startswith(">"):
                continue

            # 解析里程碑（二级标题）
            if line.startswith("## "):
                if current_milestone:
                    milestones.append(current_milestone)

                milestone_name = line[2:].strip()
                # 去掉可能的表情符号
                if milestone_name.startswith("🏁 "):
                    milestone_name = milestone_name[2:].strip()

                current_milestone = {
                    "id": f"M{len(milestones) + 1}",
                    "name": milestone_name,
                    "description": "",
                    "status": "planned",
                    "tasks": [],
                }

            # 解析任务（列表项）
            elif line.startswith("- ") and current_milestone:
                task_line = line[2:].strip()
                task_title = task_line
                task_status = "planned"

                # 解析状态表情
                if task_line.startswith("🟢"):
                    task_status = "todo"
                    task_title = task_line[1:].strip()
                elif task_line.startswith("✅"):
                    task_status = "completed"
                    task_title = task_line[1:].strip()

                # 解析链接格式 [标题](链接)
                if "[" in task_title and "](" in task_title:
                    link_start = task_title.find("[")
                    link_mid = task_title.find("](")
                    link_end = task_title.find(")", link_mid)

                    if link_start >= 0 and link_mid > link_start and link_end > link_mid:
                        task_title = task_title[link_start + 1 : link_mid]

                # 解析状态标签 `状态`
                if "`" in task_title:
                    status_start = task_title.rfind("`")
                    status_end = task_title.rfind("`", status_start + 1)

                    if status_start >= 0 and status_end > status_start:
                        status_text = task_title[status_start + 1 : status_end]
                        task_title = task_title[:status_start].strip()

                        # 映射状态文本
                        if status_text.lower() in ["进行中", "in progress"]:
                            task_status = "in_progress"

                # 添加任务
                current_milestone["tasks"].append(
                    {
                        "id": f"{current_milestone['id']}-{len(current_milestone['tasks']) + 1}",
                        "title": task_title,
                        "description": f"从路线图导入的任务: {task_title}",
                        "milestone": current_milestone["id"],
                        "status": task_status,
                        "priority": "P2",  # 默认中等优先级
                        "assignees": [],
                    }
                )

        # 添加最后一个里程碑
        if current_milestone:
            milestones.append(current_milestone)

        return {"title": title, "description": description, "milestones": milestones}

    def import_to_github(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """将路线图数据导入到GitHub.

        Args:
            data: 路线图数据

        Returns:
            Dict[str, Any]: 导入结果
        """
        # 1. 创建标签
        self._create_labels()

        # 2. 创建里程碑
        for milestone in data.get("milestones", []):
            self._create_milestone(milestone)

        # 3. 创建Issues
        for milestone in data.get("milestones", []):
            for task in milestone.get("tasks", []):
                milestone_number = self.milestone_map.get(task["milestone"])
                if milestone_number:
                    self._create_issue(task, milestone_number)

        # 4. 创建项目
        project_id, project_number = self._create_project(data["title"], data["description"])

        if project_id:
            # 5. 添加自定义字段
            self._add_custom_fields(project_id)

            # 6. 将Issues添加到项目
            self._add_items_to_project(project_id, data)

        return {
            "project_id": project_id,
            "project_number": project_number,
            "issues": len(self.issue_map),
            "milestones": len(self.milestone_map),
        }

    def _create_labels(self) -> None:
        """在GitHub仓库创建必要的标签."""
        # 优先级标签
        priority_labels = [
            {"name": "priority:critical", "color": "b60205", "description": "P0 - 最高优先级，阻塞性问题"},
            {"name": "priority:high", "color": "d93f0b", "description": "P1 - 高优先级，重要功能"},
            {"name": "priority:medium", "color": "fbca04", "description": "P2 - 中等优先级，常规功能"},
            {"name": "priority:low", "color": "0e8a16", "description": "P3 - 低优先级，非关键功能"},
        ]

        # 状态标签
        status_labels = [
            {"name": "status:completed", "color": "0e8a16", "description": "已完成的任务"},
            {"name": "status:in-progress", "color": "1d76db", "description": "正在进行中的任务"},
            {"name": "status:todo", "color": "c2e0c6", "description": "待办的任务"},
            {"name": "status:planned", "color": "d4c5f9", "description": "已计划但尚未开始的任务"},
        ]

        # 里程碑标签前缀
        milestone_labels = [
            {"name": "milestone:M1", "color": "5319e7", "description": "里程碑1相关任务"},
            {"name": "milestone:M2", "color": "5319e7", "description": "里程碑2相关任务"},
            {"name": "milestone:M3", "color": "5319e7", "description": "里程碑3相关任务"},
            {"name": "milestone:M4", "color": "5319e7", "description": "里程碑4相关任务"},
            {"name": "milestone:M5", "color": "5319e7", "description": "里程碑5相关任务"},
        ]

        print("创建标签...")
        all_labels = priority_labels + status_labels + milestone_labels
        for label in all_labels:
            try:
                response = self.issues_client.create_label(
                    self.owner, self.repo, label["name"], label["color"], label["description"]
                )
                if response:
                    print(f"  创建标签: {label['name']}")
            except Exception as e:
                # 标签可能已存在，忽略错误
                print(f"  跳过标签 {label['name']}: {str(e)}")

    def _create_milestone(self, milestone_data: Dict[str, Any]) -> Optional[int]:
        """在GitHub仓库创建里程碑.

        Args:
            milestone_data: 里程碑数据

        Returns:
            Optional[int]: 创建的里程碑编号
        """
        milestone_id = milestone_data["id"]
        title = f"{milestone_id}: {milestone_data['name']}"
        description = milestone_data.get("description", "")
        state = "open" if milestone_data.get("status") != "completed" else "closed"

        # 处理日期，如果有的话
        due_on = None
        if "end_date" in milestone_data:
            due_on = milestone_data["end_date"]

        print(f"创建里程碑: {title}")
        try:
            response = self.issues_client.create_milestone(
                self.owner, self.repo, title, state, description, due_on
            )

            if response and "number" in response:
                milestone_number = response["number"]
                self.milestone_map[milestone_id] = milestone_number
                return milestone_number
        except Exception as e:
            print(f"  创建里程碑失败: {str(e)}")

        return None

    def _create_issue(
        self, task_data: Dict[str, Any], milestone_number: int
    ) -> Optional[Dict[str, Any]]:
        """在GitHub仓库创建Issue.

        Args:
            task_data: 任务数据
            milestone_number: 里程碑编号

        Returns:
            Optional[Dict[str, Any]]: 创建的Issue
        """
        # 根据优先级映射标签
        priority_labels = {
            "P0": "priority:critical",
            "P1": "priority:high",
            "P2": "priority:medium",
            "P3": "priority:low",
        }

        # 根据状态映射标签
        status_labels = {
            "completed": "status:completed",
            "in_progress": "status:in-progress",
            "todo": "status:todo",
            "planned": "status:planned",
        }

        # 准备标签
        labels = [
            f"milestone:{task_data['milestone']}",
            priority_labels.get(task_data.get("priority", "P2"), "priority:medium"),
            status_labels.get(task_data.get("status", "planned"), "status:planned"),
        ]

        task_id = task_data["id"]
        title = f"{task_id}: {task_data['title']}"
        body = task_data.get("description", f"任务: {task_data['title']}")
        assignees = task_data.get("assignees", [])

        print(f"创建Issue: {title}")
        try:
            response = self.issues_client.create_issue(
                self.owner, self.repo, title, body, assignees, milestone_number, labels
            )

            if response:
                self.issue_map[task_id] = response
                return response
        except Exception as e:
            print(f"  创建Issue失败: {str(e)}")

        return None

    def _create_project(self, title: str, description: str) -> Tuple[Optional[str], Optional[int]]:
        """创建GitHub Project.

        Args:
            title: 项目标题
            description: 项目描述

        Returns:
            Tuple[Optional[str], Optional[int]]: 项目ID和编号
        """
        print(f"创建项目: {title}")
        try:
            # 创建项目
            response = self.projects_client.create_project(
                self.owner, self.repo, title, description
            )

            if response and "id" in response:
                project_id = response["id"]
                project_number = response.get("number", 0)
                print(f"  项目创建成功，ID: {project_id}, 编号: {project_number}")
                return project_id, project_number
        except Exception as e:
            print(f"  创建项目失败: {str(e)}")

        return None, None

    def _add_custom_fields(self, project_id: str) -> None:
        """创建并添加自定义字段到项目.

        Args:
            project_id: GitHub项目ID
        """
        # 使用_create_custom_fields方法创建自定义字段
        self.field_map = self._create_custom_fields(project_id)

        # 打印创建的字段信息
        print(f"已创建 {len(self.field_map)} 个自定义字段:")
        for field_name, field_id in self.field_map.items():
            print(f"  - {field_name}: {field_id}")

    def _add_items_to_project(self, project_id: str, data: Dict[str, Any]) -> None:
        """将Issues添加到项目.

        Args:
            project_id: 项目ID
            data: 路线图数据
        """
        print("将Issues添加到项目...")

        # 获取字段值映射
        status_map = {"completed": "已完成", "in_progress": "进行中", "todo": "待办", "planned": "已计划"}

        priority_map = {"P0": "P0 - 紧急", "P1": "P1 - 高", "P2": "P2 - 中", "P3": "P3 - 低"}

        # 添加所有Issues到项目，并设置自定义字段值
        for milestone in data.get("milestones", []):
            for task in milestone.get("tasks", []):
                task_id = task["id"]
                if task_id not in self.issue_map:
                    continue

                issue = self.issue_map[task_id]
                issue_id = issue.get("node_id")

                if not issue_id:
                    continue

                try:
                    # 添加到项目
                    print(f"  添加Issue到项目: {task['title']}")
                    success = self.projects_client.add_issue_to_project(
                        self.owner, self.repo, project_id, issue_id
                    )

                    if not success:
                        print(f"    添加失败: 无法添加Issue {task_id}")
                        continue

                    # 找到项目中的条目ID
                    item_id = self._find_project_item_id(project_id, issue_id)
                    if not item_id:
                        print(f"    设置字段失败: 无法找到项目条目ID")
                        continue

                    # 设置里程碑字段
                    if "milestone" in self.field_map and "milestone" in task:
                        self._set_field_value(
                            project_id, item_id, self.field_map["milestone"], task["milestone"]
                        )

                    # 设置状态字段
                    if "status" in self.field_map and "status" in task:
                        self._set_field_value(
                            project_id,
                            item_id,
                            self.field_map["status"],
                            status_map.get(task["status"], "已计划"),
                        )

                    # 设置优先级字段
                    if "priority" in self.field_map and "priority" in task:
                        self._set_field_value(
                            project_id,
                            item_id,
                            self.field_map["priority"],
                            priority_map.get(task["priority"], "P2 - 中"),
                        )

                except Exception as e:
                    print(f"    处理Issue出错: {str(e)}")

    def _find_project_item_id(self, project_id: str, content_id: str) -> Optional[str]:
        """查找项目中条目的ID.

        Args:
            project_id: 项目ID
            content_id: 内容ID (如Issue的node_id)

        Returns:
            Optional[str]: 项目条目ID
        """
        # 这个功能需要额外实现，当前API客户端中可能没有封装
        # 需要通过GraphQL API查询
        return None

    def _set_field_value(self, project_id: str, item_id: str, field_id: str, value: str) -> bool:
        """设置项目条目的字段值.

        Args:
            project_id: 项目ID
            item_id: 项目条目ID
            field_id: 字段ID
            value: 字段值

        Returns:
            bool: 是否成功
        """
        # 需要通过项目客户端进行设置
        try:
            return self.projects_client.update_project_item_field(
                project_id, item_id, field_id, value
            )
        except Exception:
            return False

    def _create_custom_fields(self, project_id: str) -> Dict[str, str]:
        """创建自定义字段.

        Args:
            project_id: GitHub项目ID

        Returns:
            Dict[str, str]: 字段名称到字段ID的映射
        """
        fields = {}
        print("创建自定义字段...")

        # 创建里程碑字段
        milestone_field_id = self.projects_client.add_field(
            project_id=project_id,
            name="里程碑",
            field_type="SINGLE_SELECT",
            options=[{"name": f"M{i}", "color": "PURPLE"} for i in range(1, 6)],
        )
        if milestone_field_id:
            fields["milestone"] = milestone_field_id
            print("  创建里程碑字段成功")

        # 创建状态字段
        status_field_id = self.projects_client.add_field(
            project_id=project_id,
            name="状态",
            field_type="SINGLE_SELECT",
            options=[
                {"name": "已完成", "color": "GREEN"},
                {"name": "进行中", "color": "BLUE"},
                {"name": "待办", "color": "YELLOW"},
                {"name": "已计划", "color": "PURPLE"},
            ],
        )
        if status_field_id:
            fields["status"] = status_field_id
            print("  创建状态字段成功")

        # 创建优先级字段
        priority_field_id = self.projects_client.add_field(
            project_id=project_id,
            name="优先级",
            field_type="SINGLE_SELECT",
            options=[
                {"name": "P0 - 紧急", "color": "RED"},
                {"name": "P1 - 高", "color": "ORANGE"},
                {"name": "P2 - 中", "color": "YELLOW"},
                {"name": "P3 - 低", "color": "GREEN"},
            ],
        )
        if priority_field_id:
            fields["priority"] = priority_field_id
            print("  创建优先级字段成功")

        # 创建开始日期字段
        start_date_field_id = self.projects_client.add_field(
            project_id=project_id, name="开始日期", field_type="DATE"
        )
        if start_date_field_id:
            fields["start_date"] = start_date_field_id
            print("  创建开始日期字段成功")

        # 创建结束日期字段
        end_date_field_id = self.projects_client.add_field(
            project_id=project_id, name="结束日期", field_type="DATE"
        )
        if end_date_field_id:
            fields["end_date"] = end_date_field_id
            print("  创建结束日期字段成功")

        return fields


def main() -> None:
    """主函数."""
    parser = argparse.ArgumentParser(description="导入路线图数据到GitHub Projects")
    parser.add_argument("--owner", help="GitHub仓库所有者", default=os.environ.get("GITHUB_OWNER"))
    parser.add_argument("--repo", help="GitHub仓库名称", default=os.environ.get("GITHUB_REPO"))
    parser.add_argument("--file", help="路线图数据文件路径", required=True)
    parser.add_argument("--token", help="GitHub令牌", default=os.environ.get("GITHUB_TOKEN"))

    args = parser.parse_args()

    # 检查必要参数
    if not args.owner:
        print("错误: 未提供仓库所有者。请使用--owner参数或设置GITHUB_OWNER环境变量")
        sys.exit(1)

    if not args.repo:
        print("错误: 未提供仓库名称。请使用--repo参数或设置GITHUB_REPO环境变量")
        sys.exit(1)

    if not args.token:
        print("错误: 未提供GitHub令牌。请使用--token参数或设置GITHUB_TOKEN环境变量")
        sys.exit(1)

    # 初始化导入工具
    importer = RoadmapImporter(args.owner, args.repo, args.token)

    # 加载数据
    data = importer.load_data(args.file)

    # 导入到GitHub
    result = importer.import_to_github(data)

    # 打印结果
    print("\n导入完成:")
    print(f"  项目编号: #{result['project_number']}")
    print(f"  里程碑数: {result['milestones']}")
    print(f"  任务数: {result['issues']}")


if __name__ == "__main__":
    # 尝试加载.env文件中的环境变量
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    main()
