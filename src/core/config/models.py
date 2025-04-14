"""
配置模型定义模块

提供配置系统中使用的基础类、枚举和异常定义。
"""

import logging
import os
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

# 配置日志
logger = logging.getLogger(__name__)

# 类型变量定义
T = TypeVar("T")


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


class ConfigValue(Generic[T]):
    """配置值包装器，支持环境变量覆盖"""

    def __init__(self, default: T, env_key: Optional[str] = None, validator: Optional[callable] = None):
        self.default = default
        self.env_key = env_key
        self.validator = validator

    def _clean_env_value(self, value: str) -> str:
        """清理环境变量值，移除注释和多余空格"""
        # 移除注释
        if "#" in value:
            value = value.split("#")[0]
        # 移除首尾空格
        return value.strip()

    def get_value(self) -> T:
        """获取配置值，优先使用环境变量"""
        if self.env_key and self.env_key in os.environ:
            value = self._clean_env_value(os.environ[self.env_key])

            # 如果清理后的值为空，使用默认值
            if not value:
                return self.default

            # 根据默认值类型进行转换
            try:
                if isinstance(self.default, bool):
                    value = value.lower() in ("true", "1", "yes")
                elif isinstance(self.default, int):
                    value = int(value)
                elif isinstance(self.default, float):
                    value = float(value)
                elif isinstance(self.default, list):
                    value = [v.strip() for v in value.split(",") if v.strip()]
            except (ValueError, TypeError) as e:
                logger.warning(f"环境变量 {self.env_key} 值转换失败: {e}")
                return self.default

            # 验证值
            if self.validator and not self.validator(value):
                logger.warning(f"环境变量 {self.env_key} 值验证失败")
                return self.default

            return value
        return self.default
