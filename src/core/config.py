"""
VibeCopilot配置管理模块

负责处理应用程序的配置，包括：
1. 配置文件读写
2. 默认配置生成
3. 配置验证
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "app": {
        "name": "VibeCopilot",
        "version": "0.1.0",
        "log_level": "INFO",
    },
    "paths": {
        "templates_dir": "templates",
        "data_dir": "data",
        "output_dir": "output",
    },
    "database": {
        "path": ".ai/vibecopilot.db",
        "type": "sqlite",
        "debug": False,
    },
    "ai": {
        "default_provider": "openai",
        "openai": {
            "api_key_env": "OPENAI_API_KEY",
            "default_model": "gpt-4",
            "temperature": 0.7,
        },
        "cursor": {
            "enabled": True,
        },
    },
    "features": {
        "enable_command_line": True,
        "enable_mcp": True,
        "enable_web_ui": False,
    },
}


class ConfigManager:
    """配置管理器类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.config_dir = self._get_config_dir()
        self.config_path = config_path or os.path.join(self.config_dir, "config.json")
        self.config = self._load_config()

    def _get_config_dir(self) -> str:
        """
        获取配置目录，优先使用环境变量，否则使用默认位置

        Returns:
            配置目录路径
        """
        if os.environ.get("VIBECOPILOT_CONFIG_DIR"):
            config_dir = os.environ.get("VIBECOPILOT_CONFIG_DIR")
        else:
            # 默认使用用户主目录下的.vibecopilot文件夹
            config_dir = os.path.join(Path.home(), ".vibecopilot")

        # 确保目录存在
        os.makedirs(config_dir, exist_ok=True)
        return config_dir

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置，如果配置文件存在则读取，否则使用默认配置

        Returns:
            配置字典
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    logger.info(f"配置已从 {self.config_path} 加载")
                    # 合并默认配置，确保所有必要的键存在
                    return self._merge_configs(DEFAULT_CONFIG, config)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                logger.info("使用默认配置")
                return DEFAULT_CONFIG.copy()
        else:
            logger.info(f"配置文件不存在，使用默认配置: {self.config_path}")
            # 保存默认配置
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()

    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归合并默认配置和用户配置

        Args:
            default: 默认配置
            user: 用户配置

        Returns:
            合并后的配置
        """
        result = default.copy()

        for key, value in user.items():
            # 如果用户配置中的值是字典，且默认配置中也有该键，则递归合并
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                # 否则直接使用用户配置的值
                result[key] = value

        return result

    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        保存配置到文件

        Args:
            config: 配置字典

        Returns:
            保存是否成功
        """
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"配置已保存到 {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置

        Returns:
            配置字典
        """
        return self.config

    def update_config(self, new_config: Dict[str, Any], save: bool = True) -> Dict[str, Any]:
        """
        更新配置

        Args:
            new_config: 新配置，将与现有配置合并
            save: 是否保存到文件

        Returns:
            更新后的配置
        """
        self.config = self._merge_configs(self.config, new_config)
        if save:
            self.save_config(self.config)
        return self.config

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        通过点分隔的路径获取配置值

        Args:
            key_path: 以点分隔的配置路径，如'app.name'
            default: 如果路径不存在，返回的默认值

        Returns:
            配置值或默认值
        """
        keys = key_path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any, save: bool = True) -> bool:
        """
        通过点分隔的路径设置配置值

        Args:
            key_path: 以点分隔的配置路径，如'app.name'
            value: 要设置的值
            save: 是否保存到文件

        Returns:
            设置是否成功
        """
        keys = key_path.split(".")
        config = self.config

        # 导航到最后一个键之前的所有键
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # 设置最后一个键的值
        config[keys[-1]] = value

        if save:
            return self.save_config(self.config)
        return True


# 全局配置实例
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """
    获取全局配置管理器实例

    Returns:
        ConfigManager实例
    """
    return config_manager
