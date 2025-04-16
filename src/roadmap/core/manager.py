"""
路线图管理器模块

提供路线图核心管理功能，用于处理路线图数据的业务逻辑。
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import yaml

from src.core.config import get_config
from src.models.db.roadmap import Roadmap
from src.utils.file_utils import ensure_directory_exists

logger = logging.getLogger(__name__)

# 常量定义（如果需要）
DEFAULT_ROADMAP_ID = "current"


class RoadmapManager:
    """管理路线图的加载、保存和访问"""

    def __init__(self):
        """初始化路线图管理器"""
        self.config = get_config()
        self.project_root = self.config.get("paths.project_root", os.getcwd())
        self.agent_work_dir = self.config.get("paths.agent_work_dir", ".ai")  # 从配置获取
        # 使用 agent_work_dir 构建 roadmap 数据目录
        self.roadmap_data_dir = os.path.join(self.project_root, self.agent_work_dir, "roadmap")
        ensure_directory_exists(self.roadmap_data_dir)

        # 从配置获取默认 roadmap 文件名
        self.default_roadmap_file = self.config.get("github.roadmap_data_file", "roadmap/current.yaml")
        # 确保 default_roadmap_file 是相对于 agent_work_dir 的
        if not os.path.isabs(self.default_roadmap_file) and self.default_roadmap_file.startswith("roadmap/"):
            self.default_roadmap_file = self.default_roadmap_file[len("roadmap/") :]  # 移除前缀

        # roadmap 缓存
        self.roadmaps: Dict[str, Roadmap] = {}
        self.current_roadmap_id: Optional[str] = None
        self._load_current_roadmap_id()

    def _get_roadmap_file_path(self, roadmap_id: str) -> str:
        """获取指定路线图ID的文件路径"""
        # 确保文件名安全
        safe_filename = f"{roadmap_id.replace('/', '_').replace('..', '')}.yaml"
        return os.path.join(self.roadmap_data_dir, safe_filename)

    def _load_current_roadmap_id(self):
        """加载当前活动的路线图ID"""
        # 可以从一个状态文件或配置中加载
        # 简化处理：暂时默认使用 default_roadmap_file 对应的 ID
        # 解析 default_roadmap_file 获取 ID
        if self.default_roadmap_file.endswith(".yaml"):
            self.current_roadmap_id = self.default_roadmap_file[:-5]  # 移除 .yaml 后缀
        else:
            self.current_roadmap_id = DEFAULT_ROADMAP_ID

    def get_roadmap(self, roadmap_id: Optional[str] = None) -> Optional[Roadmap]:
        """获取路线图，如果未指定ID，则获取当前活动的路线图"""
        target_id = roadmap_id or self.current_roadmap_id
        if not target_id:
            # 尝试加载默认的
            target_id = DEFAULT_ROADMAP_ID
            if self.default_roadmap_file.endswith(".yaml"):
                target_id = self.default_roadmap_file[:-5]
            self.current_roadmap_id = target_id  # 设置为当前

        if target_id in self.roadmaps:
            return self.roadmaps[target_id]

        # 从文件加载
        file_path = self._get_roadmap_file_path(target_id)
        # 直接使用 yaml 库加载
        roadmap = None
        try:
            if not os.path.exists(file_path):
                logger.warning(f"路线图文件未找到: {file_path}")
                return None
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                logger.warning(f"路线图文件为空或格式错误: {file_path}")
                return None
            # 假设 Roadmap 类支持从字典初始化
            roadmap = Roadmap(**data)
            # 如果 Roadmap 没有 id 属性，或者 id 不在 data 中，需要设置
            if not hasattr(roadmap, "id") or not roadmap.id:
                roadmap.id = target_id
        except yaml.YAMLError as e:
            logger.error(f"解析路线图文件失败: {file_path} - {e}")
            return None
        except FileNotFoundError:
            logger.warning(f"路线图文件未找到: {file_path}")
            return None
        except Exception as e:
            logger.error(f"加载路线图时发生未知错误: {file_path} - {e}", exc_info=True)
            return None

        if roadmap:
            self.roadmaps[target_id] = roadmap
            return roadmap
        return None

    def save_roadmap(self, roadmap: Roadmap, roadmap_id: Optional[str] = None) -> bool:
        """保存路线图到文件"""
        target_id = roadmap_id or roadmap.id
        if not target_id:
            target_id = DEFAULT_ROADMAP_ID  # Fallback ID
            roadmap.id = target_id  # Assign ID if missing

        file_path = self._get_roadmap_file_path(target_id)
        ensure_directory_exists(os.path.dirname(file_path))

        roadmap_data = roadmap.to_dict()  # 假设有 to_dict 方法
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(roadmap_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            # 更新缓存
            self.roadmaps[target_id] = roadmap
            return True
        except Exception as e:
            # 添加日志
            print(f"错误：保存路线图失败 ({file_path}): {e}", file=os.sys.stderr)
            return False

    def set_current_roadmap(self, roadmap_id: str) -> bool:
        """设置当前活动的路线图"""
        # 验证 roadmap_id 是否存在（可选）
        file_path = self._get_roadmap_file_path(roadmap_id)
        if not os.path.exists(file_path):
            # 或者尝试加载 self.get_roadmap(roadmap_id)
            print(f"错误：路线图文件不存在: {file_path}", file=os.sys.stderr)
            return False

        self.current_roadmap_id = roadmap_id
        # 可以将当前ID持久化到状态文件
        return True

    def get_current_roadmap_id(self) -> Optional[str]:
        """获取当前活动的路线图ID"""
        return self.current_roadmap_id

    def list_available_roadmaps(self) -> List[str]:
        """列出所有可用的路线图ID"""
        available_ids = []
        try:
            for filename in os.listdir(self.roadmap_data_dir):
                if filename.endswith(".yaml"):
                    roadmap_id = filename[:-5]  # 移除 .yaml 后缀
                    available_ids.append(roadmap_id)
        except FileNotFoundError:
            pass  # 目录不存在则返回空列表
        except Exception as e:
            print(f"错误：列出路线图失败: {e}", file=os.sys.stderr)

        return available_ids

    def check_roadmap(
        self,
        check_type: str = "roadmap",
        resource_id: Optional[str] = None,
        roadmap_id: Optional[str] = None,
        update: bool = False,
    ) -> Dict[str, Any]:
        """
        检查路线图状态

        Args:
            check_type: 检查类型
            resource_id: 资源ID
            update: 是否更新

        Returns:
            Dict[str, Any]: 检查结果
        """
        roadmap_id = roadmap_id or self.current_roadmap_id

        # 处理不同类型的检查
        if check_type == "roadmap" or check_type == "entire":
            return self._check_entire_roadmap(roadmap_id, update)
        elif check_type == "milestone":
            return self._check_milestone(roadmap_id, resource_id, update)
        elif check_type == "task":
            return self._check_task(roadmap_id, resource_id, update)
        else:
            raise ValueError(f"不支持的检查类型: {check_type}")

    def _check_entire_roadmap(self, roadmap_id: str, update: bool) -> Dict[str, Any]:
        """检查整个路线图状态"""
        # 获取所有数据
        roadmap = self.get_roadmap(roadmap_id)
        if not roadmap:
            raise ValueError(f"未找到路线图: {roadmap_id}")

        milestones = roadmap.milestones
        tasks = roadmap.tasks

        # 计算任务统计信息
        task_status = {"todo": 0, "in_progress": 0, "completed": 0}
        for task in tasks:
            status = task.get("status", "todo")
            if status in task_status:
                task_status[status] += 1

        # 计算活跃里程碑
        active_milestone = None
        milestone_status = {}
        for milestone in milestones:
            milestone_id = milestone.get("id")
            milestone_status[milestone_id] = {
                "name": milestone.get("name"),
                "status": milestone.get("status", "planned"),
                "progress": milestone.get("progress", 0),
                "tasks": len([t for t in tasks if t.get("milestone") == milestone_id]),
            }

            if milestone.get("status") == "in_progress":
                active_milestone = milestone_id

        # 如果没有活跃里程碑但有里程碑，选择第一个
        if not active_milestone and milestones:
            active_milestone = milestones[0].get("id")

        return {
            "milestones": len(milestones),
            "tasks": len(tasks),
            "active_milestone": active_milestone,
            "milestone_status": milestone_status,
            "task_status": task_status,
        }

    def _check_milestone(self, roadmap_id: str, milestone_id: Optional[str], update: bool) -> Dict[str, Any]:
        """检查特定里程碑状态"""
        if not milestone_id:
            raise ValueError("检查里程碑需要指定id参数")

        # 查找里程碑
        roadmap = self.get_roadmap(roadmap_id)
        if not roadmap:
            raise ValueError(f"未找到路线图: {roadmap_id}")

        milestone = None
        for m in roadmap.milestones:
            if m.get("id") == milestone_id:
                milestone = m
                break

        if not milestone:
            raise ValueError(f"未找到里程碑: {milestone_id}")

        # 获取里程碑任务
        tasks = roadmap.tasks
        milestone_tasks = [t for t in tasks if t.get("milestone") == milestone_id]

        # 计算任务状态
        task_status = {"todo": 0, "in_progress": 0, "completed": 0}
        for task in tasks:
            status = task.get("status", "todo")
            if status in task_status:
                task_status[status] += 1

        # 计算进度
        total_tasks = len(tasks)
        completed_tasks = task_status.get("completed", 0)
        progress = int(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # 更新里程碑进度 - 简化实现
        if update and milestone:
            milestone_data = milestone.copy()
            milestone_data["progress"] = progress

            # 自动更新状态
            if progress == 100:
                milestone_data["status"] = "completed"
            elif progress > 0:
                milestone_data["status"] = "in_progress"

            # 这里不再更新数据库，因为我们现在只是一个模拟实现
            logger.info(f"里程碑进度更新: {milestone_id} -> {progress}%")

        return {
            "milestone_id": milestone_id,
            "name": milestone.get("name"),
            "status": milestone.get("status"),
            "progress": progress,
            "tasks": total_tasks,
            "task_status": task_status,
        }

    def _check_task(self, roadmap_id: str, task_id: Optional[str], update: bool) -> Dict[str, Any]:
        """检查特定任务状态"""
        if not task_id:
            raise ValueError("检查任务需要指定id参数")

        # 查找任务 - 简化实现
        roadmap = self.get_roadmap(roadmap_id)
        if not roadmap:
            raise ValueError(f"未找到路线图: {roadmap_id}")

        task = None
        for t in roadmap.tasks:
            if t.get("id") == task_id:
                task = t
                break

        if not task:
            raise ValueError(f"未找到任务: {task_id}")

        # 查找关联里程碑
        milestone = None
        milestone_id = task.get("milestone")
        if milestone_id:
            milestones = roadmap.milestones
            for m in milestones:
                if m.get("id") == milestone_id:
                    milestone = m
                    break

        return {
            "task_id": task_id,
            "title": task.get("title"),
            "status": task.get("status"),
            "priority": task.get("priority", "medium"),
            "milestone": {
                "id": milestone_id,
                "name": milestone.get("name") if milestone else None,
                "status": milestone.get("status") if milestone else None,
            }
            if milestone_id
            else None,
        }
