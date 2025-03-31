"""
VibeCopilot状态管理模块

负责跟踪和管理项目的状态，包括：
1. 项目阶段跟踪
2. 任务状态管理
3. 进度报告
"""

import os
import json
import logging
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime

from .config import get_config

# 配置日志
logger = logging.getLogger(__name__)

class ProjectPhase(Enum):
    """项目阶段枚举"""
    SETUP = "setup"           # 准备与配置
    PLANNING = "planning"     # 规划与设计
    DEVELOPMENT = "development" # 开发与执行
    TESTING = "testing"       # 测试与质量保证
    MANAGEMENT = "management" # 项目管理与维护

class TaskStatus(Enum):
    """任务状态枚举"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

class StateManager:
    """项目状态管理器"""

    def __init__(self, project_path: Optional[str] = None):
        """
        初始化状态管理器

        Args:
            project_path: 项目路径，如果为None则使用当前工作目录
        """
        self.config = get_config()
        self.project_path = project_path or os.getcwd()
        self.state_file = os.path.join(self.project_path, ".vibecopilot", "state.json")
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """
        加载项目状态，如果状态文件存在则读取，否则初始化新状态

        Returns:
            状态字典
        """
        # 确保状态文件所在目录存在
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    logger.info(f"项目状态已从 {self.state_file} 加载")
                    return state
            except Exception as e:
                logger.error(f"加载状态文件失败: {e}")
                logger.info("初始化新状态")
                return self._initialize_state()
        else:
            logger.info(f"状态文件不存在，初始化新状态: {self.state_file}")
            state = self._initialize_state()
            self.save_state(state)
            return state

    def _initialize_state(self) -> Dict[str, Any]:
        """
        初始化新的项目状态

        Returns:
            初始状态字典
        """
        # 获取项目名称，默认使用目录名
        project_name = os.path.basename(os.path.abspath(self.project_path))

        # 初始化各阶段的任务
        phases = {}
        for phase in ProjectPhase:
            phases[phase.value] = {
                "status": TaskStatus.NOT_STARTED.value if phase != ProjectPhase.SETUP else TaskStatus.IN_PROGRESS.value,
                "progress": 0,
                "tasks": {}
            }

        # 为每个阶段添加默认任务
        phases[ProjectPhase.SETUP.value]["tasks"] = {
            "development_tools": {
                "status": TaskStatus.NOT_STARTED.value,
                "description": "选择开发工具",
                "progress": 0,
                "updated_at": datetime.now().isoformat()
            },
            "ai_rules": {
                "status": TaskStatus.NOT_STARTED.value,
                "description": "配置AI规则",
                "progress": 0,
                "updated_at": datetime.now().isoformat()
            },
            "project_docs": {
                "status": TaskStatus.NOT_STARTED.value,
                "description": "建立项目级知识库",
                "progress": 0,
                "updated_at": datetime.now().isoformat()
            },
            "dev_environment": {
                "status": TaskStatus.NOT_STARTED.value,
                "description": "搭建开发环境",
                "progress": 0,
                "updated_at": datetime.now().isoformat()
            }
        }

        # 初始化状态
        return {
            "project": {
                "name": project_name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "current_phase": ProjectPhase.SETUP.value,
                "overall_progress": 0
            },
            "phases": phases,
            "documents": {
                "prd": {
                    "status": "not_created",
                    "updated_at": None
                },
                "app_flow": {
                    "status": "not_created",
                    "updated_at": None
                },
                "tech_stack": {
                    "status": "not_created",
                    "updated_at": None
                }
            }
        }

    def save_state(self, state: Dict[str, Any]) -> bool:
        """
        保存状态到文件

        Args:
            state: 状态字典

        Returns:
            保存是否成功
        """
        try:
            # 更新时间戳
            state["project"]["updated_at"] = datetime.now().isoformat()

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"项目状态已保存到 {self.state_file}")
            return True
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")
            return False

    def get_state(self) -> Dict[str, Any]:
        """
        获取当前项目状态

        Returns:
            状态字典
        """
        return self.state

    def get_current_phase(self) -> str:
        """
        获取当前项目阶段

        Returns:
            当前阶段名称
        """
        return self.state["project"]["current_phase"]

    def advance_phase(self) -> bool:
        """
        将项目推进到下一阶段

        Returns:
            操作是否成功
        """
        current_phase = self.get_current_phase()

        # 查找当前阶段的索引
        try:
            current_index = [p.value for p in ProjectPhase].index(current_phase)

            # 如果不是最后一个阶段，则前进到下一阶段
            if current_index < len(ProjectPhase) - 1:
                next_phase = [p.value for p in ProjectPhase][current_index + 1]

                # 将当前阶段标记为已完成
                self.state["phases"][current_phase]["status"] = TaskStatus.COMPLETED.value
                self.state["phases"][current_phase]["progress"] = 100

                # 将下一阶段标记为进行中
                self.state["phases"][next_phase]["status"] = TaskStatus.IN_PROGRESS.value

                # 更新当前阶段
                self.state["project"]["current_phase"] = next_phase

                # 重新计算总体进度
                self._recalculate_progress()

                # 保存状态
                return self.save_state(self.state)
            else:
                logger.info("已经是最后一个阶段，无法前进")
                return False

        except ValueError:
            logger.error(f"无效的阶段: {current_phase}")
            return False

    def set_task_status(self, phase: str, task_id: str, status: TaskStatus, progress: int = None) -> bool:
        """
        设置任务状态

        Args:
            phase: 阶段名称
            task_id: 任务ID
            status: 新状态
            progress: 新进度，如果为None则根据状态自动设置

        Returns:
            操作是否成功
        """
        if phase not in self.state["phases"]:
            logger.error(f"无效的阶段: {phase}")
            return False

        if task_id not in self.state["phases"][phase]["tasks"]:
            logger.error(f"阶段 {phase} 中不存在任务 {task_id}")
            return False

        # 更新任务状态
        self.state["phases"][phase]["tasks"][task_id]["status"] = status.value

        # 如果未指定进度，则根据状态设置默认进度
        if progress is None:
            if status == TaskStatus.COMPLETED:
                progress = 100
            elif status == TaskStatus.IN_PROGRESS:
                # 如果之前是未开始，则设为10%，否则保持原进度
                if self.state["phases"][phase]["tasks"][task_id]["progress"] == 0:
                    progress = 10
            elif status == TaskStatus.NOT_STARTED:
                progress = 0

        # 如果提供了进度，则更新
        if progress is not None:
            self.state["phases"][phase]["tasks"][task_id]["progress"] = progress

        # 更新任务更新时间
        self.state["phases"][phase]["tasks"][task_id]["updated_at"] = datetime.now().isoformat()

        # 重新计算阶段进度
        self._recalculate_phase_progress(phase)

        # 重新计算总体进度
        self._recalculate_progress()

        # 保存状态
        return self.save_state(self.state)

    def add_task(self, phase: str, task_id: str, description: str) -> bool:
        """
        添加新任务

        Args:
            phase: 阶段名称
            task_id: 任务ID
            description: 任务描述

        Returns:
            操作是否成功
        """
        if phase not in self.state["phases"]:
            logger.error(f"无效的阶段: {phase}")
            return False

        if task_id in self.state["phases"][phase]["tasks"]:
            logger.warning(f"任务 {task_id} 已存在于阶段 {phase}")
            return False

        # 添加新任务
        self.state["phases"][phase]["tasks"][task_id] = {
            "status": TaskStatus.NOT_STARTED.value,
            "description": description,
            "progress": 0,
            "updated_at": datetime.now().isoformat()
        }

        # 重新计算阶段进度
        self._recalculate_phase_progress(phase)

        # 重新计算总体进度
        self._recalculate_progress()

        # 保存状态
        return self.save_state(self.state)

    def update_document_status(self, doc_type: str, status: str) -> bool:
        """
        更新文档状态

        Args:
            doc_type: 文档类型 (prd, app_flow, tech_stack等)
            status: 新状态 (not_created, in_progress, created)

        Returns:
            操作是否成功
        """
        if doc_type not in self.state["documents"]:
            logger.error(f"无效的文档类型: {doc_type}")
            return False

        # 更新文档状态
        self.state["documents"][doc_type]["status"] = status
        self.state["documents"][doc_type]["updated_at"] = datetime.now().isoformat()

        # 保存状态
        return self.save_state(self.state)

    def _recalculate_phase_progress(self, phase: str) -> None:
        """
        重新计算阶段进度

        Args:
            phase: 阶段名称
        """
        tasks = self.state["phases"][phase]["tasks"]

        if not tasks:
            # 如果没有任务，则进度为0
            self.state["phases"][phase]["progress"] = 0
            return

        # 计算平均进度
        total_progress = sum(task["progress"] for task in tasks.values())
        average_progress = total_progress / len(tasks)

        # 更新阶段进度
        self.state["phases"][phase]["progress"] = round(average_progress)

        # 如果所有任务都已完成，则将阶段状态设为已完成
        if all(task["status"] == TaskStatus.COMPLETED.value for task in tasks.values()):
            self.state["phases"][phase]["status"] = TaskStatus.COMPLETED.value
        # 如果有任务在进行中，则将阶段状态设为进行中
        elif any(task["status"] == TaskStatus.IN_PROGRESS.value for task in tasks.values()):
            self.state["phases"][phase]["status"] = TaskStatus.IN_PROGRESS.value

    def _recalculate_progress(self) -> None:
        """重新计算项目总体进度"""
        phases = self.state["phases"]

        # 计算阶段权重
        weights = {
            ProjectPhase.SETUP.value: 0.1,
            ProjectPhase.PLANNING.value: 0.2,
            ProjectPhase.DEVELOPMENT.value: 0.4,
            ProjectPhase.TESTING.value: 0.2,
            ProjectPhase.MANAGEMENT.value: 0.1
        }

        # 计算加权进度
        weighted_progress = sum(
            phases[phase]["progress"] * weights[phase]
            for phase in phases
        )

        # 更新总体进度
        self.state["project"]["overall_progress"] = round(weighted_progress)

    def get_phase_tasks(self, phase: str) -> Dict[str, Dict[str, Any]]:
        """
        获取阶段任务

        Args:
            phase: 阶段名称

        Returns:
            任务字典
        """
        if phase not in self.state["phases"]:
            logger.error(f"无效的阶段: {phase}")
            return {}

        return self.state["phases"][phase]["tasks"]

    def get_progress_report(self) -> Dict[str, Any]:
        """
        获取进度报告

        Returns:
            进度报告字典
        """
        return {
            "project_name": self.state["project"]["name"],
            "current_phase": self.state["project"]["current_phase"],
            "overall_progress": self.state["project"]["overall_progress"],
            "phases": {
                phase: {
                    "status": self.state["phases"][phase]["status"],
                    "progress": self.state["phases"][phase]["progress"],
                    "task_count": len(self.state["phases"][phase]["tasks"]),
                    "completed_tasks": sum(
                        1 for task in self.state["phases"][phase]["tasks"].values()
                        if task["status"] == TaskStatus.COMPLETED.value
                    )
                }
                for phase in self.state["phases"]
            },
            "documents": self.state["documents"]
        }
