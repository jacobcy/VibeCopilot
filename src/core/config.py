"""
VibeCopilot配置管理模块

提供统一的配置管理，支持：
1. 多级配置(环境变量 > 配置文件 > 默认配置)
2. 配置验证和类型检查
3. 路径标准化和验证
4. 配置热重载
"""

import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """配置相关错误的基类"""

    pass


class ConfigValidationError(ConfigError):
    """配置验证错误"""

    pass


class ConfigPathError(ConfigError):
    """配置路径错误"""

    pass


class ConfigEnvironment(Enum):
    """配置环境枚举"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

    @classmethod
    def from_string(cls, value: str) -> "ConfigEnvironment":
        """从字符串创建环境枚举"""
        try:
            return cls(value.lower())
        except ValueError:
            logger.warning(f"未知的环境值: {value}，使用开发环境")
            return cls.DEVELOPMENT


T = TypeVar("T")


class ConfigValue(Generic[T]):
    """配置值包装器，支持环境变量覆盖"""

    def __init__(self, default: T, env_key: Optional[str] = None, validator: Optional[callable] = None):
        self.default = default
        self.env_key = env_key
        self.validator = validator

    def get_value(self) -> T:
        """获取配置值，优先使用环境变量"""
        if self.env_key and self.env_key in os.environ:
            value = os.environ[self.env_key]
            # 根据默认值类型进行转换
            try:
                if isinstance(self.default, bool):
                    value = value.lower() in ("true", "1", "yes")
                elif isinstance(self.default, int):
                    value = int(value)
                elif isinstance(self.default, float):
                    value = float(value)
                elif isinstance(self.default, list):
                    value = value.split(",")
            except (ValueError, TypeError) as e:
                logger.warning(f"环境变量 {self.env_key} 值转换失败: {e}")
                return self.default

            # 验证值
            if self.validator and not self.validator(value):
                logger.warning(f"环境变量 {self.env_key} 值验证失败")
                return self.default

            return value
        return self.default


# 默认配置定义
DEFAULT_CONFIG = {
    "app": {
        "name": ConfigValue("VibeCopilot", env_key="APP_NAME"),
        "version": ConfigValue("0.1.0", env_key="APP_VERSION"),
        "environment": ConfigValue(
            ConfigEnvironment.DEVELOPMENT.value,
            env_key="APP_ENV",
            validator=lambda x: x in [e.value for e in ConfigEnvironment],
        ),
        "log_level": ConfigValue("INFO", env_key="LOG_LEVEL"),
        "debug": ConfigValue(True, env_key="DEBUG"),
    },
    "paths": {
        "project_root": ConfigValue(str(Path.cwd()), env_key="PROJECT_ROOT"),
        "templates_dir": ConfigValue("templates"),
        "data_dir": ConfigValue("data"),
        "output_dir": ConfigValue("output"),
        "docs_source_dir": ConfigValue("docs", env_key="DOCS_SOURCE_DIR"),
        "obsidian_vault_dir": ConfigValue(".obsidian/vault", env_key="OBSIDIAN_VAULT_DIR"),
        "docs_engine_db": ConfigValue("data/docs_engine.db", env_key="DOCS_ENGINE_DB_PATH"),
        "docs_vector_db": ConfigValue("data/docs_vector.db", env_key="DOCS_VECTOR_DB_PATH"),
    },
    "database": {
        "url": ConfigValue("sqlite:///data/vibecopilot.db", env_key="DATABASE_URL"),
        "type": ConfigValue("sqlite"),
        "debug": ConfigValue(False, env_key="DB_DEBUG"),
    },
    "ai": {
        "provider": ConfigValue("openai", env_key="AI_PROVIDER"),
        "model": ConfigValue("gpt-4", env_key="AI_MODEL"),
        "temperature": ConfigValue(0.7, env_key="AI_TEMPERATURE"),
        "openai": {
            "api_key": ConfigValue(None, env_key="OPENAI_API_KEY"),
        },
        "anthropic": {
            "api_key": ConfigValue(None, env_key="ANTHROPIC_API_KEY"),
        },
    },
    "features": {
        "enable_command_line": ConfigValue(True),
        "enable_mcp": ConfigValue(True),
        "enable_web_ui": ConfigValue(False),
    },
    "sync": {
        "auto_sync_docs": ConfigValue(False, env_key="AUTO_SYNC_DOCS"),
        "auto_sync_interval": ConfigValue(300, env_key="AUTO_SYNC_INTERVAL"),
    },
}


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
                logger.info(f"已从 {self.config_path} 加载配置")
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
        """通过点分隔的路径获取配置值"""
        value = self.config
        try:
            for key in key_path.split("."):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any, save: bool = True) -> bool:
        """通过点分隔的路径设置配置值"""
        keys = key_path.split(".")
        config = self.config

        # 导航到最后一个键之前的所有键
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            elif not isinstance(config[key], dict):
                raise ConfigError(f"配置路径 {key_path} 无效：{key} 不是字典")
            config = config[key]

        # 设置值
        config[keys[-1]] = value

        # 如果设置的是路径，确保它是绝对路径
        if key_path.startswith("paths.") and key_path != "paths.project_root":
            self._validate_paths()

        return self.save_config(self.config) if save else True

    def reload(self):
        """重新加载配置"""
        self.config = self._load_config()
        self._validate_paths()

    def get_environment(self) -> ConfigEnvironment:
        """获取当前环境"""
        env_str = self.get("app.environment", ConfigEnvironment.DEVELOPMENT.value)
        return ConfigEnvironment.from_string(env_str)

    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.get_environment() == ConfigEnvironment.DEVELOPMENT

    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.get_environment() == ConfigEnvironment.PRODUCTION

    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.get_environment() == ConfigEnvironment.TESTING


# 全局配置实例
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """获取全局配置管理器实例"""
    return config_manager
