"""
路线图生成器核心功能

提供生成和更新GitHub项目路线图的主要功能。
这是原始roadmap_generator.py的核心组件。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .formatters import format_roadmap_data

# 导入新的模块化组件
from .templates import apply_template, get_roadmap_template
from .validators import validate_roadmap_data


class RoadmapGenerator:
    """路线图生成器"""

    def __init__(self, github_client=None, config=None):
        """
        初始化路线图生成器

        Args:
            github_client: GitHub API客户端
            config: 生成器配置
        """
        self.github_client = github_client
        self.config = config or {}

    def generate_roadmap(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成路线图

        Args:
            data: 路线图数据

        Returns:
            Dict[str, Any]: 生成的路线图
        """
        # 1. 验证数据
        validate_roadmap_data(data)

        # 2. 应用模板
        template = get_roadmap_template(data.get("template", "default"))
        roadmap_data = apply_template(data, template)

        # 3. 生成路线图
        return self._generate_roadmap_impl(roadmap_data)

    def _generate_roadmap_impl(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        路线图生成核心实现

        Args:
            data: 处理后的路线图数据

        Returns:
            Dict[str, Any]: 生成的路线图
        """
        # 简化后的核心生成逻辑
        roadmap = {
            "title": data.get("title", "Project Roadmap"),
            "description": data.get("description", ""),
            "milestones": self._generate_milestones(data.get("milestones", [])),
            "tasks": self._generate_tasks(data.get("tasks", [])),
            "generated_at": datetime.now().isoformat(),
        }

        # 格式化输出
        return format_roadmap_data(roadmap)

    def _generate_milestones(self, milestones_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成里程碑数据"""
        milestones = []
        for m_data in milestones_data:
            # 简化的里程碑处理逻辑
            milestone = {
                "id": m_data.get("id", f"m-{len(milestones)+1}"),
                "name": m_data.get("name", f"Milestone {len(milestones)+1}"),
                "start_date": m_data.get("start_date"),
                "end_date": m_data.get("end_date"),
                "description": m_data.get("description", ""),
                "progress": self._calculate_milestone_progress(m_data),
            }
            milestones.append(milestone)
        return milestones

    def _generate_tasks(self, tasks_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成任务数据"""
        tasks = []
        for t_data in tasks_data:
            # 简化的任务处理逻辑
            task = {
                "id": t_data.get("id", f"t-{len(tasks)+1}"),
                "title": t_data.get("title", f"Task {len(tasks)+1}"),
                "description": t_data.get("description", ""),
                "milestone": t_data.get("milestone"),
                "assignees": t_data.get("assignees", []),
                "status": t_data.get("status", "pending"),
            }
            tasks.append(task)
        return tasks

    def _calculate_milestone_progress(self, milestone_data: Dict[str, Any]) -> int:
        """
        计算里程碑进度

        如果有显式设置进度，则使用该值；
        否则，根据任务完成情况计算进度。

        Args:
            milestone_data: 里程碑数据

        Returns:
            int: 进度百分比
        """
        # 如果有显式设置的进度，直接使用
        if "progress" in milestone_data:
            return int(milestone_data["progress"])

        # 简化的进度计算逻辑
        return 0  # 默认值，实际实现会根据任务状态计算
