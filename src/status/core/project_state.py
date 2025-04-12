"""
项目状态管理模块

管理项目全局状态，如当前阶段、活动工作流等
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ProjectState:
    """项目状态管理器

    管理项目全局状态，包括当前阶段、活动工作流等
    """

    def __init__(self):
        """初始化项目状态管理器"""
        self._project_state = {
            "name": "未命名项目",
            "current_phase": "planning",  # planning, development, testing, review, release
            "active_workflow": None,
            "features_count": 0,
            "tasks_count": 0,
            "version": "0.1.0",
        }

        # 加载已保存的项目状态
        self._load_project_state()

    def _load_project_state(self):
        """从文件加载项目状态"""
        try:
            # 确保状态目录存在
            status_dir = os.path.join(os.path.expanduser("~"), "data/temp", "status")
            if not os.path.exists(status_dir):
                os.makedirs(status_dir)

            # 读取状态文件
            status_file = os.path.join(status_dir, "project_state.json")
            if os.path.exists(status_file):
                with open(status_file, "r", encoding="utf-8") as f:
                    saved_state = json.load(f)
                    # 更新状态，但保留未保存的键
                    for key, value in saved_state.items():
                        self._project_state[key] = value
                    logger.info(f"已加载项目状态，当前阶段: {self._project_state['current_phase']}")
        except Exception as e:
            logger.warning(f"加载项目状态时出错: {e}")

    def _save_project_state(self):
        """保存项目状态到文件"""
        try:
            # 确保状态目录存在
            status_dir = os.path.join(os.path.expanduser("~"), "data/temp", "status")
            if not os.path.exists(status_dir):
                os.makedirs(status_dir)

            # 保存状态文件
            status_file = os.path.join(status_dir, "project_state.json")
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(self._project_state, f, indent=2, ensure_ascii=False)
                logger.info(f"已保存项目状态，当前阶段: {self._project_state['current_phase']}")
        except Exception as e:
            logger.warning(f"保存项目状态时出错: {e}")

    def get_project_state(self) -> Dict[str, Any]:
        """获取项目状态

        Returns:
            项目状态数据
        """
        return self._project_state.copy()

    def get_current_phase(self) -> str:
        """获取当前项目阶段

        Returns:
            当前阶段名称
        """
        return self._project_state.get("current_phase", "planning")

    def update_state(self, key: str, value: Any) -> Dict[str, Any]:
        """更新项目状态

        Args:
            key: 状态键
            value: 状态值

        Returns:
            更新后的状态
        """
        if key in self._project_state:
            old_value = self._project_state[key]
            self._project_state[key] = value
            logger.info(f"项目状态已更新: {key} = {value} (原值: {old_value})")
        else:
            logger.warning(f"未知项目状态键: {key}")
            self._project_state[key] = value

        self._save_project_state()

        return self.get_project_state()

    def update_project_phase(self, phase: str) -> Dict[str, Any]:
        """更新项目阶段

        Args:
            phase: 新的项目阶段

        Returns:
            更新结果
        """
        valid_phases = ["planning", "development", "testing", "review", "release"]

        if phase not in valid_phases:
            logger.warning(f"无效的项目阶段: {phase}")
            return {"updated": False, "error": f"无效的项目阶段: {phase}，有效值为 {', '.join(valid_phases)}"}

        old_phase = self._project_state.get("current_phase")

        if old_phase == phase:
            logger.info(f"项目已经处于 {phase} 阶段")
            return {"updated": False, "old_phase": old_phase, "message": f"项目已经处于 {phase} 阶段"}

        self._project_state["current_phase"] = phase
        logger.info(f"项目阶段已更新: {old_phase} -> {phase}")

        self._save_project_state()

        return {
            "updated": True,
            "old_phase": old_phase,
            "new_phase": phase,
            "message": f"项目阶段已更新为 {phase}",
        }

    def initialize_project(self, project_name: str) -> Dict[str, Any]:
        """初始化项目状态

        Args:
            project_name: 项目名称

        Returns:
            初始化结果
        """
        self._project_state = {
            "name": project_name,
            "current_phase": "planning",
            "active_workflow": None,
            "features_count": 0,
            "tasks_count": 0,
            "version": "0.1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        logger.info(f"项目 {project_name} 已初始化")

        self._save_project_state()

        return {"initialized": True, "name": project_name, "message": f"项目 {project_name} 已初始化"}

    @staticmethod
    def _get_current_time() -> str:
        """获取当前时间字符串

        Returns:
            str: ISO格式的时间字符串
        """
        return datetime.now().isoformat()
