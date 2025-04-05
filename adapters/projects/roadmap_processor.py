#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路线图数据处理模块.

用于处理和转换GitHub Projects数据为路线图格式。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..api import GitHubProjectsClient


class RoadmapProcessor:
    """路线图数据处理器."""

    def __init__(self, client: Optional[GitHubProjectsClient] = None):
        """初始化路线图处理器.

        Args:
            client: GitHub Projects API客户端，如果未提供则创建一个新实例
        """
        self.client = client or GitHubProjectsClient()

    def process_roadmap_data(
        self, data: Dict[str, Any]
    ) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
        """处理路线图数据.

        从GitHub Projects API响应中提取路线图数据。

        Args:
            data: API响应数据

        Returns:
            Dict: 处理后的路线图数据，包含项目信息和任务列表
        """
        if not data or "data" not in data:
            return {"title": "无数据", "description": "无法获取路线图数据", "tasks": []}

        project_data = data.get("data", {}).get("repository", {}).get("projectV2", {})
        if not project_data:
            return {"title": "无数据", "description": "项目数据为空", "tasks": []}

        title = project_data.get("title", "未命名路线图")
        description = project_data.get("shortDescription", "无描述")
        url = project_data.get("url", "")

        tasks = []
        milestones = []

        # 处理项目条目
        items = project_data.get("items", {}).get("nodes", [])
        for item in items:
            task_data = self._extract_task_data(item)
            if task_data:
                if self._is_milestone(task_data):
                    milestones.append(task_data)
                else:
                    tasks.append(task_data)

        # 按里程碑分组任务
        grouped_tasks = self._group_tasks_by_milestone(tasks, milestones)

        return {
            "title": title,
            "description": description,
            "url": url,
            "tasks": grouped_tasks,
        }

    def _extract_task_data(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从项目条目中提取任务数据.

        Args:
            item: 项目条目数据

        Returns:
            Optional[Dict[str, Any]]: 提取的任务数据，如果无法提取则返回None
        """
        if not item or "content" not in item:
            return None

        content = item.get("content", {})
        if not content:
            return None

        # 基本信息
        task = {
            "id": item.get("id", ""),
            "title": content.get("title", "未命名任务"),
            "state": content.get("state", "OPEN"),
            "number": content.get("number", 0),
            "url": content.get("url", ""),
            "created_at": self._format_date(content.get("createdAt")),
            "updated_at": self._format_date(content.get("updatedAt")),
            "labels": [],
            "assignees": [],
            "milestone": None,
            "status": None,
            "due_date": None,
        }

        # 处理标签
        labels = content.get("labels", {}).get("nodes", [])
        for label in labels:
            task["labels"].append(
                {
                    "name": label.get("name", ""),
                    "color": label.get("color", ""),
                }
            )

        # 处理指派人
        assignees = content.get("assignees", {}).get("nodes", [])
        for assignee in assignees:
            task["assignees"].append(assignee.get("login", ""))

        # 处理自定义字段
        field_values = item.get("fieldValues", {}).get("nodes", [])
        for field_value in field_values:
            field_name = field_value.get("field", {}).get("name", "").lower()

            if field_name == "status" and "name" in field_value:
                task["status"] = field_value.get("name")
            elif field_name == "milestone" and "name" in field_value:
                task["milestone"] = field_value.get("name")
            elif field_name == "due date" and "date" in field_value:
                task["due_date"] = self._format_date(field_value.get("date"))
            elif "text" in field_value:
                # 处理其他文本字段
                field_name = field_value.get("field", {}).get("name", "").lower()
                if field_name:
                    task[field_name] = field_value.get("text")

        return task

    def _is_milestone(self, task: Dict[str, Any]) -> bool:
        """判断任务是否为里程碑.

        根据标签或其他特征判断。

        Args:
            task: 任务数据

        Returns:
            bool: 是否为里程碑
        """
        # 检查标签
        for label in task.get("labels", []):
            if label.get("name", "").lower() in ["milestone", "里程碑"]:
                return True

        # 检查标题格式（通常里程碑会以特定格式命名）
        title = task.get("title", "").lower()
        milestone_prefixes = ["milestone:", "milestone -", "里程碑:", "里程碑 -"]
        for prefix in milestone_prefixes:
            if title.startswith(prefix):
                return True

        return False

    def _group_tasks_by_milestone(
        self, tasks: List[Dict[str, Any]], milestones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """按里程碑分组任务.

        Args:
            tasks: 任务列表
            milestones: 里程碑列表

        Returns:
            List[Dict[str, Any]]: 分组后的任务
        """
        # 创建里程碑映射
        milestone_map = {}
        result = []

        # 先添加所有里程碑
        for milestone in milestones:
            milestone_item = {
                "id": milestone.get("id"),
                "title": milestone.get("title"),
                "type": "milestone",
                "state": milestone.get("state"),
                "due_date": milestone.get("due_date"),
                "tasks": [],
            }
            milestone_name = milestone.get("title")
            if milestone_name:
                milestone_map[milestone_name] = milestone_item
            result.append(milestone_item)

        # 将任务分配到里程碑
        unassigned_tasks = []
        for task in tasks:
            milestone_name = task.get("milestone")
            if milestone_name and milestone_name in milestone_map:
                # 添加到对应里程碑
                milestone_map[milestone_name]["tasks"].append({**task, "type": "task"})
            else:
                # 未分配里程碑的任务
                unassigned_tasks.append({**task, "type": "task"})

        # 添加未分配里程碑的任务
        if unassigned_tasks:
            result.append(
                {
                    "id": "unassigned",
                    "title": "未分配里程碑",
                    "type": "category",
                    "tasks": unassigned_tasks,
                }
            )

        return result

    def _format_date(self, date_str: Optional[str]) -> Optional[str]:
        """格式化日期字符串.

        Args:
            date_str: ISO格式的日期字符串

        Returns:
            Optional[str]: 格式化后的日期字符串，如果输入为None则返回None
        """
        if not date_str:
            return None

        try:
            date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date_obj.strftime("%Y-%m-%d")
        except Exception:
            return date_str


if __name__ == "__main__":
    # 使用示例
    client = GitHubProjectsClient()
    processor = RoadmapProcessor(client)

    try:
        # 获取项目数据
        owner = "octocat"
        repo = "hello-world"
        project_number = 1

        project_data = client.get_project_v2(owner, repo, project_number)
        if project_data:
            roadmap = processor.process_roadmap_data(project_data)
            print(f"路线图标题: {roadmap.get('title')}")
            print(f"任务数量: {len(roadmap.get('tasks', []))}")
    except Exception as e:
        print(f"处理失败: {e}")
