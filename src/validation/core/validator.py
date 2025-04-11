"""
验证器基类定义

提供验证器基类和核心功能
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Validator(ABC):
    """验证器基类，所有验证器应该继承此类"""

    def __init__(self):
        """初始化验证器"""
        self.warnings = []
        self.errors = []

    @abstractmethod
    def validate(self, data: Any) -> bool:
        """
        验证数据

        Args:
            data: 要验证的数据

        Returns:
            bool: 验证是否通过
        """
        pass

    def get_warnings(self) -> List[str]:
        """获取警告信息列表"""
        return self.warnings

    def get_errors(self) -> List[str]:
        """获取错误信息列表"""
        return self.errors

    def clear_messages(self):
        """清空警告和错误信息"""
        self.warnings = []
        self.errors = []
