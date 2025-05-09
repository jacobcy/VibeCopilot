from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union


class StatusSource(Enum):
    """配置来源枚举"""

    PROJECT_STATE = "project_state"  # 项目状态后端
    ENV_VARIABLE = "env_variable"  # 环境变量
    SETTINGS_JSON = "settings_json"  # 设置文件
    GIT_DETECTION = "git_detection"  # Git检测
    FALLBACK = "fallback"  # 默认值

    def __str__(self):
        return self.value

    @staticmethod
    def get_display_name(source_value):
        """获取适合显示的来源名称"""
        source_map = {
            StatusSource.PROJECT_STATE.value: "项目状态配置",
            StatusSource.ENV_VARIABLE.value: "环境变量",
            StatusSource.SETTINGS_JSON.value: "settings.json配置文件",
            StatusSource.GIT_DETECTION.value: "Git仓库检测",
            StatusSource.FALLBACK.value: "未知来源",
        }
        return source_map.get(source_value, "未知来源")


class StatusProvider:
    """状态提供者抽象基类"""

    def get_domain(self) -> str:
        """获取状态领域"""
        raise NotImplementedError

    def get_status(self) -> Dict[str, Any]:
        """获取状态数据"""
        raise NotImplementedError
