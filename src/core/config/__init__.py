"""
配置管理包

提供配置的加载、验证和管理功能。
这个子包将原来的config.py拆分为多个模块，实现了更好的模块化和代码组织。
"""

from src.core.config.manager import ConfigManager, get_config
from src.core.config.models import ConfigEnvironment, ConfigError, ConfigPathError, ConfigValidationError, ConfigValue

__all__ = [
    # 配置管理器
    "ConfigManager",
    "get_config",
    # 配置模型
    "ConfigEnvironment",
    "ConfigError",
    "ConfigPathError",
    "ConfigValidationError",
    "ConfigValue",
]
