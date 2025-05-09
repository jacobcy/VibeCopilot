"""
项目状态核心模块

维护和管理VibeCopilot项目的全局状态，包括活动路线图、GitHub关联等信息。
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from src.core.config.settings import SettingsConfig

logger = logging.getLogger(__name__)

# 状态文件路径
STATE_DIR = ".vibecopilot/status"
PROJECT_STATE_FILE = os.path.join(STATE_DIR, "project_state.json")


def get_default_state() -> Dict[str, Any]:
    """返回默认的项目状态结构"""
    return {
        "name": "VibeCopilot",
        "current_phase": "planning",
        "current_roadmap_id": "",
        "current_task_id": "",
        "last_updated": datetime.now().isoformat(),
        "active_roadmap_backend_config": {},
        "roadmap_github_mapping": {},
    }


class ProjectState:
    """项目状态管理类"""

    def __init__(self, settings_config: Optional[SettingsConfig] = None):
        """初始化项目状态"""
        self.settings_config = settings_config
        self._state_data: Dict[str, Any] = {}
        self._load_state()

    def _load_state(self) -> None:
        """加载项目状态文件"""
        # 确保目录存在
        os.makedirs(STATE_DIR, exist_ok=True)

        if os.path.exists(PROJECT_STATE_FILE):
            try:
                with open(PROJECT_STATE_FILE, "r", encoding="utf-8") as f:
                    self._state_data = json.load(f)
                    logger.debug(f"已加载项目状态文件: {PROJECT_STATE_FILE}")
            except Exception as e:
                logger.error(f"加载项目状态文件失败: {e}")
                self._state_data = get_default_state()
                self._save_state()  # 保存初始状态
        else:
            logger.info(f"未找到项目状态文件，创建默认状态")
            self._state_data = get_default_state()
            self._save_state()  # 保存初始状态

    def _save_state(self) -> None:
        """保存项目状态到文件"""
        try:
            # 更新最后修改时间
            self._state_data["last_updated"] = datetime.now().isoformat()

            # 确保路径存在
            os.makedirs(STATE_DIR, exist_ok=True)

            # 保存文件
            with open(PROJECT_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._state_data, f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"已保存项目状态到文件: {PROJECT_STATE_FILE}")
        except Exception as e:
            logger.error(f"保存项目状态文件失败: {e}")

    def get_project_name(self) -> str:
        """获取项目名称

        从状态文件获取项目名称，如果不存在则从settings.json获取
        """
        # 优先从状态文件获取
        if "name" in self._state_data and self._state_data["name"]:
            return self._state_data["name"]

        # 其次从settings.json获取
        if self.settings_config:
            return self.settings_config.get("project_name", "VibeCopilot")

        return "VibeCopilot"  # 默认值

    def set_project_name(self, name: str) -> None:
        """设置项目名称"""
        self._state_data["name"] = name
        self._save_state()

    def get_current_phase(self) -> str:
        """获取当前项目阶段"""
        return self._state_data.get("current_phase", "planning")

    def set_current_phase(self, phase: str) -> None:
        """设置当前项目阶段"""
        self._state_data["current_phase"] = phase
        self._save_state()

    def get_current_roadmap_id(self) -> str:
        """获取当前活动路线图ID"""
        return self._state_data.get("current_roadmap_id", "")

    def set_current_roadmap_id(self, roadmap_id: str) -> None:
        """设置当前活动路线图ID"""
        self._state_data["current_roadmap_id"] = roadmap_id
        self._save_state()

    def get_current_task_id(self) -> str:
        """获取当前活动任务ID"""
        return self._state_data.get("current_task_id", "")

    def set_current_task_id(self, task_id: Optional[str]) -> bool:
        """设置当前活动任务ID"""
        try:
            self._state_data["current_task_id"] = task_id if task_id is not None else ""
            self._save_state()
            logger.info(f"ProjectState: 当前任务ID已设置为: {self._state_data['current_task_id']}")
            return True
        except Exception as e:
            logger.error(f"ProjectState: 设置当前任务ID时出错: {e}", exc_info=True)
            return False

    def get_active_roadmap_backend_config(self) -> Dict[str, Any]:
        """获取当前活动路线图的后端配置"""
        return self._state_data.get("active_roadmap_backend_config", {})

    def set_active_roadmap_backend_config(self, config: Dict[str, Any]) -> None:
        """设置当前活动路线图的后端配置"""
        self._state_data["active_roadmap_backend_config"] = config
        self._save_state()

    def get_github_project_id_for_roadmap(self, roadmap_id: str) -> Optional[str]:
        """获取路线图对应的GitHub Project ID"""
        roadmap_github_mapping = self._state_data.get("roadmap_github_mapping", {})
        return roadmap_github_mapping.get(roadmap_id)

    def set_roadmap_github_project(self, roadmap_id: str, github_project_id: str) -> None:
        """设置路线图对应的GitHub Project ID

        注意：这里确保一个GitHub项目只能与一个本地路线图关联
        """
        if "roadmap_github_mapping" not in self._state_data:
            self._state_data["roadmap_github_mapping"] = {}

        # 检查该GitHub项目是否已与其他路线图关联
        for existing_roadmap_id, existing_project_id in list(self._state_data["roadmap_github_mapping"].items()):
            if existing_project_id == github_project_id and existing_roadmap_id != roadmap_id:
                # 如果该GitHub项目已与其他路线图关联，移除旧关联
                logger.warning(f"GitHub项目 {github_project_id} 已与路线图 {existing_roadmap_id} 关联，现移除旧关联并建立新关联到 {roadmap_id}")
                del self._state_data["roadmap_github_mapping"][existing_roadmap_id]

        # 建立新关联
        self._state_data["roadmap_github_mapping"][roadmap_id] = github_project_id
        self._save_state()

    def get_all_roadmap_github_mappings(self) -> Dict[str, str]:
        """获取所有路线图与GitHub项目的映射关系"""
        return self._state_data.get("roadmap_github_mapping", {})

    def remove_roadmap_github_mapping(self, roadmap_id: str) -> None:
        """移除特定路线图的GitHub Project映射"""
        if "roadmap_github_mapping" in self._state_data and roadmap_id in self._state_data["roadmap_github_mapping"]:
            del self._state_data["roadmap_github_mapping"][roadmap_id]
            self._save_state()
            logger.info(f"已移除路线图 {roadmap_id} 的GitHub Project映射")

    def sync_settings_to_state(self) -> None:
        """同步settings.json中的配置到状态文件"""
        if not self.settings_config:
            logger.warning("未提供settings_config，无法同步配置")
            return

        # 同步项目名称（如果settings中有设置）
        if self.settings_config.get("project_name"):
            self._state_data["name"] = self.settings_config.get("project_name")

        self._save_state()
        logger.info("已同步settings配置到项目状态文件")

    def get_project_state(self) -> Dict[str, Any]:
        """获取当前项目状态的字典表示。"""
        return self._state_data.copy()  # 返回副本以防止外部修改

    def initialize_project(self, project_name: str, github_project_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """初始化或重置项目状态。

        Args:
            project_name: 要初始化的项目名称。
            github_project_info: GitHub项目信息，包含project_id, project_title, project_number

        Returns:
            Dict[str, Any]: 初始化后的状态。
        """
        logger.info(f"正在为项目 '{project_name}' 初始化/重置状态...")
        self._state_data = get_default_state()
        self._state_data["name"] = project_name
        # 可以在这里设置其他特定于初始化的默认值
        self._state_data["current_phase"] = "planning"  # 确保初始阶段

        # 创建默认路线图并与 GitHub 项目关联
        if github_project_info and github_project_info.get("project_id") and github_project_info.get("project_title"):
            # 以 GitHub 项目名作为默认路线图 ID
            default_roadmap_id = "default-roadmap"
            self._state_data["current_roadmap_id"] = default_roadmap_id

            # 设置映射关系
            self._state_data["roadmap_github_mapping"] = {default_roadmap_id: github_project_info.get("project_id")}

            # 清空旧的后端配置，避免数据冗余
            self._state_data["active_roadmap_backend_config"] = {}

            logger.info(
                f"已创建默认路线图 '{default_roadmap_id}' 并关联到 GitHub 项目 '{github_project_info.get('project_title')}' (#{github_project_info.get('project_number')})"
            )
        else:
            # 未提供 GitHub 项目信息时，清空相关字段
            self._state_data["current_roadmap_id"] = ""
            self._state_data["active_roadmap_backend_config"] = {}
            self._state_data["roadmap_github_mapping"] = {}
            logger.info("未提供 GitHub 项目信息，没有创建默认路线图关联")

        self._save_state()
        logger.info(f"项目 '{project_name}' 状态已初始化。")
        return self._state_data.copy()
