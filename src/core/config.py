"""
配置管理模块

为了保持向后兼容性，从新的config包重新导出所有内容。
新代码应该直接导入src.core.config包内容。
"""

from src.core.config.manager import ConfigManager, get_config
from src.core.config.models import ConfigEnvironment, ConfigError, ConfigPathError, ConfigValidationError, ConfigValue

__all__ = [
    "ConfigManager",
    "get_config",
    "ConfigEnvironment",
    "ConfigError",
    "ConfigPathError",
    "ConfigValidationError",
    "ConfigValue",
]
