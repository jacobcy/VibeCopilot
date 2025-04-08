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


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_dir = self._get_config_dir()
        self.config_path = Path(config_path) if config_path else Path(self.config_dir) / "config.json"
        self.config = self._load_config()
        self._validate_paths()

    def _get_config_dir(self) -> Path:
        """获取配置目录

        优先使用环境变量VIBECOPILOT_CONFIG_DIR，否则使用用户主目录下的.vibecopilot
        """
        config_dir = os.environ.get("VIBECOPILOT_CONFIG_DIR")
        if config_dir:
            path = Path(config_dir)
        else:
            path = Path.home() / ".vibecopilot"

        path.mkdir(parents=True, exist_ok=True)
        return path

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

        按优先级加载：环境变量 > 配置文件 > 默认配置
        """
        try:
            # 首先加载默认配置
            config = self._resolve_config_values(DEFAULT_CONFIG)

            # 如果配置文件存在，加载并合并
            if self.config_path.exists():
                with open(self.config_path) as f:
                    file_config = json.load(f)
                config = self._merge_configs(config, file_config)
                logger.debug(f"已从 {self.config_path} 加载配置")
            else:
                logger.info(f"配置文件不存在，使用默认配置: {self.config_path}")
                self.save_config(config)

            return config

        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise ConfigError(f"加载配置失败: {e}")

    def _validate_paths(self):
        """验证并标准化所有路径配置"""
        paths = self.config.get("paths", {})
        project_root = Path(paths.get("project_root", Path.cwd()))

        for key, path in paths.items():
            if key == "project_root":
                continue

            # 转换为绝对路径
            if not os.path.isabs(path):
                abs_path = project_root / path
                self.config["paths"][key] = str(abs_path)

            # 确保父目录存在
            Path(self.config["paths"][key]).parent.mkdir(parents=True, exist_ok=True)

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并配置字典"""
        merged = base.copy()

        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged

    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"配置已保存到 {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

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

    def set(self, key_path: str, value: Any, save: bool = True) -> bool:
        """设置配置值

        支持使用点符号访问嵌套配置，如'database.url'
        """
        parts = key_path.split(".")
        target = self.config

        # 遍历路径直到最后一个部分
        for i, part in enumerate(parts[:-1]):
            if part not in target:
                # 自动创建中间节点
                target[part] = {}
            elif not isinstance(target[part], dict):
                # 如果中间节点不是字典，报错
                logger.error(f"设置配置值失败：路径 {'.'.join(parts[:i+1])} 不是字典")
                return False
            target = target[part]

        # 设置最终值
        target[parts[-1]] = value

        if save:
            return self.save_config(self.config)
        return True

    def reload(self):
        """重新加载配置"""
        self.config = self._load_config()
        self._validate_paths()

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
