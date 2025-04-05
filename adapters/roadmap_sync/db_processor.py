"""
数据库路线图处理器

使用数据库作为数据源的路线图处理器。
"""

import os
from typing import Any, Dict, List, Optional

from src.db.service import DatabaseService
from src.db.sync import DataSynchronizer

from .models import Milestone, Roadmap, Task


class DatabaseRoadmapProcessor:
    """数据库路线图处理器，使用数据库作为数据源"""

    def __init__(self, db_service: Optional[DatabaseService] = None):
        """
        初始化数据库路线图处理器

        Args:
            db_service: 数据库服务实例，如果为None则创建默认实例
        """
        # 初始化数据库服务
        self.project_path = os.environ.get("PROJECT_ROOT", os.getcwd())
        self.db_path = os.path.join(self.project_path, ".ai", "database.sqlite")
        self.db_service = db_service or DatabaseService(self.db_path)
        self.sync_service = DataSynchronizer(self.db_service, self.project_path)

        self.roadmap = None

    def read_roadmap(self) -> Roadmap:
        """
        从数据库读取路线图数据

        Returns:
            Roadmap: 路线图数据模型
        """
        # 从数据库导出数据
        data = self.db_service.export_to_yaml()
        return self._convert_data_to_roadmap(data)

    def _convert_data_to_roadmap(self, data: Dict[str, Any]) -> Roadmap:
        """将数据库导出的数据转换为Roadmap对象"""
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
            title=data.get("title", "VibeCopilot开发路线图"),
            description=data.get("description", "从数据库生成的路线图"),
            last_updated=data.get("last_updated", ""),
            milestones=milestones,
            tasks=tasks,
        )

    def write_roadmap(self, roadmap: Roadmap = None) -> bool:
        """
        将路线图数据写入数据库

        Args:
            roadmap: 路线图数据，默认使用当前加载的路线图

        Returns:
            bool: 写入是否成功
        """
        if not roadmap:
            if not self.roadmap:
                return False
            roadmap = self.roadmap

        # 将Roadmap转换为数据库格式
        data = self._convert_roadmap_to_data(roadmap)

        try:
            # 将数据导入数据库
            self.db_service.import_from_yaml(data)
            return True
        except Exception as e:
            print(f"写入数据库失败: {e}")
            return False

    def _convert_roadmap_to_data(self, roadmap: Roadmap) -> Dict[str, Any]:
        """将Roadmap对象转换为数据库导入格式"""
        # 构建里程碑数据
        milestones = []
        for milestone in roadmap.milestones:
            milestones.append(
                {
                    "id": milestone.id,
                    "name": milestone.name,
                    "description": milestone.description,
                    "start_date": milestone.start_date,
                    "end_date": milestone.end_date,
                    "status": milestone.status,
                    "progress": milestone.progress,
                }
            )

        # 构建任务数据
        tasks = []
        for task in roadmap.tasks:
            tasks.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "milestone": task.milestone,
                    "status": task.status,
                    "priority": task.priority,
                    "assignees": task.assignees,
                    "epic": task.epic,
                }
            )

        return {
            "title": roadmap.title,
            "description": roadmap.description,
            "last_updated": roadmap.last_updated,
            "milestones": milestones,
            "tasks": tasks,
        }

    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态

        Returns:
            bool: 更新是否成功
        """
        try:
            # 从数据库中获取任务
            task_data = self.db_service.get_task(task_id)
            if not task_data:
                return False

            # 更新状态
            update_data = {"status": status}
            result = self.db_service.update_task(task_id, update_data)

            # 更新进度
            self.db_service.update_progress()

            return result is not None
        except Exception as e:
            print(f"更新任务状态失败: {e}")
            return False

    def update_milestone_status(self, milestone_id: str, status: str) -> bool:
        """
        更新里程碑状态

        Args:
            milestone_id: 里程碑ID
            status: 新状态

        Returns:
            bool: 更新是否成功
        """
        try:
            # 从数据库中获取里程碑
            epic_data = self.db_service.get_epic(milestone_id)
            if not epic_data:
                return False

            # 更新状态
            update_data = {"status": status}
            result = self.db_service.update_epic(milestone_id, update_data)

            return result is not None
        except Exception as e:
            print(f"更新里程碑状态失败: {e}")
            return False

    def get_active_milestone_tasks(self) -> List[Task]:
        """
        获取当前活跃里程碑的所有任务

        Returns:
            List[Task]: 任务列表
        """
        # 读取路线图
        if not self.roadmap:
            self.roadmap = self.read_roadmap()

        # 查找活跃里程碑
        active_milestone = self.roadmap.get_active_milestone()
        if not active_milestone:
            return []

        # 返回活跃里程碑的任务
        return self.roadmap.get_tasks_by_milestone(active_milestone.id)

    def generate_new_task_id(self, milestone_id: str) -> str:
        """
        生成新的任务ID

        Args:
            milestone_id: 里程碑ID

        Returns:
            str: 新任务ID
        """
        # 从数据库查询任务
        tasks = self.db_service.list_tasks({})

        # 筛选出属于指定里程碑的任务
        milestone_tasks = []
        for task in tasks:
            story_id = task.get("story_id", "")
            if story_id and story_id.startswith("S") and story_id[1:] == milestone_id:
                milestone_tasks.append(task)

        # 找出当前最大任务编号
        max_num = 0
        for task in milestone_tasks:
            task_id = task.get("id", "")
            # 分离里程碑前缀和编号
            if "-" in task_id:
                prefix, num_str = task_id.rsplit("-", 1)
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
        # 从数据库查询所有Epic
        epics = self.db_service.list_epics()

        # 找出当前最大里程碑编号
        max_num = 0
        for epic in epics:
            epic_id = epic.get("id", "")
            # 检查ID格式是否为 "M数字" 或 "E数字"
            if len(epic_id) > 1 and epic_id[0] in ["M", "E"] and epic_id[1:].isdigit():
                num = int(epic_id[1:])
                max_num = max(max_num, num)

        # 生成新ID (保持使用M前缀以兼容旧代码)
        return f"M{max_num + 1}"

    def sync_to_file_system(self) -> Tuple[int, int]:
        """
        同步数据库到文件系统

        Returns:
            Tuple[int, int]: (同步的故事数量, 同步的任务数量)
        """
        return self.sync_service.sync_all_to_filesystem()

    def sync_from_file_system(self) -> Tuple[int, int]:
        """
        同步文件系统到数据库

        Returns:
            Tuple[int, int]: (同步的故事数量, 同步的任务数量)
        """
        return self.sync_service.sync_all_from_filesystem()

    def sync_to_yaml(self, output_path: Optional[str] = None) -> str:
        """
        同步数据库到YAML文件

        Args:
            output_path: 输出路径

        Returns:
            str: YAML文件路径
        """
        return self.sync_service.sync_to_roadmap_yaml(output_path)
