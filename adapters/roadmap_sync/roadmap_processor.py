"""
路线图处理器

简化版处理器，用于连接GitHub项目系统和Markdown解析功能。
"""

import os
from typing import Any, Dict, List, Optional

from scripts.github_project.api import GitHubClient

from .markdown_parser import load_sync_status, read_all_stories, save_sync_status
from .models import Milestone, Roadmap, Task


class RoadmapProcessor:
    """路线图处理器，简化版本主要作为Markdown和GitHub连接器"""

    def __init__(self, roadmap_path: str = None):
        """
        初始化路线图处理器

        Args:
            roadmap_path: 已废弃参数，保留是为了兼容性
        """
        self.github_client = GitHubClient()
        self.roadmap = None

    def read_roadmap(self) -> Roadmap:
        """
        从Markdown文件读取路线图数据

        Returns:
            Roadmap: 路线图数据模型
        """
        # 从Markdown读取故事数据
        data = read_all_stories()
        return self._convert_data_to_roadmap(data)

    def _convert_data_to_roadmap(self, data: Dict[str, Any]) -> Roadmap:
        """将解析的数据转换为Roadmap对象"""
        # 构建里程碑
        milestones = []
        for m_data in data.get("milestones", []):
            milestone = Milestone(
                id=m_data.get("id", ""),
                name=m_data.get("name", ""),
                description=m_data.get("description", ""),
                start_date=m_data.get("start_date", ""),
                end_date=m_data.get("end_date", ""),
                status=m_data.get("status", "planned"),
                progress=m_data.get("progress", 0),
            )
            milestones.append(milestone)

        # 构建任务
        tasks = []
        for t_data in data.get("tasks", []):
            task = Task(
                id=t_data.get("id", ""),
                title=t_data.get("title", ""),
                description=t_data.get("description", ""),
                milestone=t_data.get("milestone", ""),
                status=t_data.get("status", "todo"),
                priority=t_data.get("priority", "P2"),
                assignees=t_data.get("assignees", []),
                epic=t_data.get("epic", ""),
            )
            tasks.append(task)

        return Roadmap(
            title="VibeCopilot开发路线图",
            description="从Markdown故事生成的路线图",
            last_updated="",
            milestones=milestones,
            tasks=tasks,
        )

    def write_roadmap(self, roadmap: Roadmap = None) -> None:
        """
        向后兼容方法，不执行实际写入操作

        Args:
            roadmap: 路线图数据，默认使用当前加载的路线图
        """
        print("注意: 使用Markdown作为数据源时, 此方法不执行实际写入操作")
        return

    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        更新任务状态 (仅内存中)

        Args:
            task_id: 任务ID
            status: 新状态

        Returns:
            bool: 更新是否成功
        """
        if not self.roadmap:
            self.read_roadmap()

        task = self.roadmap.get_task_by_id(task_id)
        if not task:
            return False

        task.status = status
        self.roadmap.update_milestone_progress(task.milestone)
        return True

    def update_milestone_status(self, milestone_id: str, status: str) -> bool:
        """
        更新里程碑状态 (仅内存中)

        Args:
            milestone_id: 里程碑ID
            status: 新状态

        Returns:
            bool: 更新是否成功
        """
        if not self.roadmap:
            self.read_roadmap()

        milestone = self.roadmap.get_milestone_by_id(milestone_id)
        if not milestone:
            return False

        milestone.status = status
        return True

    def get_active_milestone_tasks(self) -> List[Task]:
        """
        获取当前活跃里程碑的所有任务

        Returns:
            List[Task]: 任务列表
        """
        if not self.roadmap:
            self.read_roadmap()

        active_milestone = self.roadmap.get_active_milestone()
        if not active_milestone:
            return []

        return self.roadmap.get_tasks_by_milestone(active_milestone.id)

    def generate_new_task_id(self, milestone_id: str) -> str:
        """
        生成新的任务ID

        Args:
            milestone_id: 里程碑ID

        Returns:
            str: 新任务ID
        """
        if not self.roadmap:
            self.read_roadmap()

        # 获取里程碑下的所有任务
        tasks = self.roadmap.get_tasks_by_milestone(milestone_id)

        # 找出当前最大任务编号
        max_num = 0
        for task in tasks:
            # 分离里程碑前缀和编号
            if "-" in task.id:
                prefix, num_str = task.id.rsplit("-", 1)
                # 如果前缀匹配且后缀是数字
                if prefix == milestone_id and num_str.isdigit():
                    num = int(num_str)
                    max_num = max(max_num, num)

        # 生成新ID
        return f"{milestone_id}-{max_num + 1}"

    def generate_new_milestone_id(self) -> str:
        """
        生成新的里程碑ID

        Returns:
            str: 新里程碑ID
        """
        if not self.roadmap:
            self.read_roadmap()

        # 找出当前最大里程碑编号
        max_num = 0
        for milestone in self.roadmap.milestones:
            # 检查ID格式是否为 "M数字"
            if len(milestone.id) > 1 and milestone.id[0] == "M" and milestone.id[1:].isdigit():
                num = int(milestone.id[1:])
                max_num = max(max_num, num)

        # 生成新ID
        return f"M{max_num + 1}"
