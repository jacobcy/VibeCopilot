"""
配置管理器模块

提供配置的加载、保存和管理功能。
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.core.config.defaults import DEFAULT_CONFIG
from src.core.config.models import ConfigEnvironment, ConfigError, ConfigValue

# 配置日志
logger = logging.getLogger(__name__)


def get_app_dir() -> Path:
    """获取应用根目录

    Returns:
        Path: 应用根目录路径
    """
    # 默认使用当前工作目录作为应用根目录
    app_dir = os.environ.get("VIBECOPILOT_APP_DIR")
    if app_dir:
        return Path(app_dir)

    # 如果没有设置环境变量，使用当前目录的父目录
    # 假设src目录位于项目根目录下
    current_file = Path(__file__)
    # 从 /path/to/src/core/config/manager.py 到 /path/to
    return current_file.parent.parent.parent.parent


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """初始化配置管理器"""
        self.config_dir = Path(".vibecopilot/config")
        self.settings_path = Path(".vibecopilot/config/settings.json")
        self.config = self._load_config()
        self._validate_paths()

    def _resolve_config_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """递归解析配置值，将ConfigValue实例转换为实际值"""
        resolved = {}
        for key, value in config.items():
            if isinstance(value, dict):
                resolved[key] = self._resolve_config_values(value)
            elif isinstance(value, ConfigValue):
                resolved[key] = value.get_value()
            else:
                resolved[key] = value
        return resolved

    def _load_config(self) -> Dict[str, Any]:
        """加载配置

        现在仅从默认配置和环境变量加载值
        """
        try:
            # 加载默认配置并解析ConfigValue (只解析环境变量)
            config = self._resolve_config_values(DEFAULT_CONFIG)

            logger.debug("已从环境变量和默认值加载配置")

            return config

        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise ConfigError(f"加载配置失败: {e}")

    def _validate_paths(self):
        """验证并标准化所有路径配置"""
        paths = self.config.get("paths", {})
        project_root_str = os.environ.get("VIBECOPILOT_APP_DIR") or str(Path.cwd())
        project_root = Path(project_root_str)

        if "paths" not in self.config:
            self.config["paths"] = {}
        self.config["paths"]["project_root"] = str(project_root)

        for key, path in paths.items():
            if key == "project_root":
                continue

            try:
                path_obj = Path(path)
                if not path_obj.is_absolute():
                    abs_path = project_root / path_obj
                    self.config["paths"][key] = str(abs_path)
                else:
                    self.config["paths"][key] = str(path_obj)
            except Exception as e:
                logger.warning(f"处理路径配置 '{key}: {path}' 时出错: {e}")

            abs_path_str = self.config["paths"].get(key, path)
            try:
                abs_path_obj = Path(abs_path_str)
                if abs_path_obj.parent and str(abs_path_obj.parent) != ".":
                    abs_path_obj.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"创建路径 '{abs_path_str}' 的父目录时出错: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值

        支持使用点符号访问嵌套配置，如'database.url'
        """
        parts = key_path.split(".")
        value = self.config
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def reload(self):
        """重新加载配置"""
        self.config = self._load_config()
        self._validate_paths()

    def refresh_config(self):
        """从环境变量刷新配置

        这个方法会重新加载所有配置，包括从环境变量、配置文件和默认值
        """
        try:
            self.config = self._load_config()
            self._validate_paths()
            logger.info("配置已成功刷新")
            return True
        except Exception as e:
            logger.error(f"刷新配置失败: {e}")
            return False

    def get_environment(self) -> ConfigEnvironment:
        """获取当前环境"""
        env_str = self.get("app.environment", ConfigEnvironment.DEVELOPMENT.value)
        return ConfigEnvironment.from_string(env_str)

    def is_development(self) -> bool:
        """检查是否为开发环境"""
        return self.get_environment() == ConfigEnvironment.DEVELOPMENT

    def is_production(self) -> bool:
        """检查是否为生产环境"""
        return self.get_environment() == ConfigEnvironment.PRODUCTION

    def is_testing(self) -> bool:
        """检查是否为测试环境"""
        return self.get_environment() == ConfigEnvironment.TESTING


# 全局配置管理器实例
_config_manager = None


def get_config() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def refresh_config():
    """刷新全局配置

    这是一个便捷函数，用于刷新全局配置管理器的配置
    """
    config_manager = get_config()
    return config_manager.refresh_config()
