"""
路线图处理器

提供roadmap.yaml文件的读取、解析和更新功能。
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

from .models import Milestone, Roadmap, Task


class RoadmapProcessor:
    """路线图处理器，处理roadmap.yaml文件的读写操作"""

    def __init__(self, roadmap_path: str = None):
        """
        初始化路线图处理器

        Args:
            roadmap_path: 路线图文件路径，默认为项目根目录下的.ai/roadmap/current.yaml
        """
        self.roadmap_path = roadmap_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            ".ai/roadmap",
            "current.yaml",
        )
        self.roadmap = None

    def read_roadmap(self) -> Roadmap:
        """
        读取路线图文件

        Returns:
            Roadmap: 路线图数据模型

        Raises:
            FileNotFoundError: 路线图文件不存在
            yaml.YAMLError: YAML解析错误
        """
        try:
            with open(self.roadmap_path, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)
                self.roadmap = Roadmap.from_dict(data)
                return self.roadmap
        except FileNotFoundError:
            raise FileNotFoundError(f"路线图文件不存在: {self.roadmap_path}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"YAML解析错误: {str(e)}")

    def write_roadmap(self, roadmap: Roadmap = None) -> None:
        """
        将路线图数据写入文件

        Args:
            roadmap: 路线图数据，默认使用当前加载的路线图

        Raises:
            ValueError: 未提供路线图数据
            IOError: 写入文件失败
        """
        if not roadmap and not self.roadmap:
            raise ValueError("未提供路线图数据")

        roadmap_to_write = roadmap or self.roadmap
        roadmap_to_write.last_updated = datetime.now().strftime("%Y-%m-%d")

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.roadmap_path), exist_ok=True)

            with open(self.roadmap_path, "w", encoding="utf-8") as file:
                yaml.dump(
                    roadmap_to_write.to_dict(),
                    file,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
        except IOError as e:
            raise IOError(f"写入路线图文件失败: {str(e)}")

    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        更新任务状态

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

        # 更新所属里程碑的进度
        self.roadmap.update_milestone_progress(task.milestone)

        # 写入文件
        self.write_roadmap()
        return True

    def update_milestone_status(self, milestone_id: str, status: str) -> bool:
        """
        更新里程碑状态

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

        # 写入文件
        self.write_roadmap()
        return True

    def add_task(self, task: Task) -> bool:
        """
        添加新任务

        Args:
            task: 任务数据

        Returns:
            bool: 添加是否成功
        """
        if not self.roadmap:
            self.read_roadmap()

        # 检查任务ID是否已存在
        if self.roadmap.get_task_by_id(task.id):
            return False

        # 添加任务
        self.roadmap.tasks.append(task)

        # 写入文件
        self.write_roadmap()
        return True

    def add_milestone(self, milestone: Milestone) -> bool:
        """
        添加新里程碑

        Args:
            milestone: 里程碑数据

        Returns:
            bool: 添加是否成功
        """
        if not self.roadmap:
            self.read_roadmap()

        # 检查里程碑ID是否已存在
        if self.roadmap.get_milestone_by_id(milestone.id):
            return False

        # 添加里程碑
        self.roadmap.milestones.append(milestone)

        # 写入文件
        self.write_roadmap()
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
        为新任务生成ID

        Args:
            milestone_id: 里程碑ID

        Returns:
            str: 新任务ID
        """
        if not self.roadmap:
            self.read_roadmap()

        # 获取里程碑下的所有任务
        milestone_tasks = self.roadmap.get_tasks_by_milestone(milestone_id)

        # 找出最大任务编号
        max_num = 0
        for task in milestone_tasks:
            # 假设任务ID格式为"T{milestone_number}.{task_number}"
            if "." in task.id:
                try:
                    task_num = int(task.id.split(".")[1])
                    max_num = max(max_num, task_num)
                except ValueError:
                    continue

        # 生成新任务ID
        return f"T{milestone_id.lstrip('M')}.{max_num + 1}"

    def generate_new_milestone_id(self) -> str:
        """
        为新里程碑生成ID

        Returns:
            str: 新里程碑ID
        """
        if not self.roadmap:
            self.read_roadmap()

        # 找出最大里程碑编号
        max_num = 0
        for milestone in self.roadmap.milestones:
            # 假设里程碑ID格式为"M{number}"
            try:
                milestone_num = int(milestone.id.lstrip("M"))
                max_num = max(max_num, milestone_num)
            except ValueError:
                continue

        # 生成新里程碑ID
        return f"M{max_num + 1}"
