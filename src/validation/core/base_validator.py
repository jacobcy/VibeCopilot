"""
基础验证器模块

提供所有验证器的基类和通用功能
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class ValidationResult:
    """验证结果类"""

    def __init__(self, is_valid: bool, data: Optional[Dict[str, Any]] = None, messages: List[str] = None):
        """
        初始化验证结果

        Args:
            is_valid: 是否验证通过
            data: 验证后的数据（可能包含自动修复的内容）
            messages: 错误/警告消息列表
        """
        self.is_valid = is_valid
        self.data = data or {}
        self.messages = messages or []

    def add_message(self, message: str) -> None:
        """
        添加消息

        Args:
            message: 错误/警告消息
        """
        if message and message not in self.messages:
            self.messages.append(message)

    def add_messages(self, messages: List[str]) -> None:
        """
        添加多个消息

        Args:
            messages: 错误/警告消息列表
        """
        if messages:
            for message in messages:
                self.add_message(message)

    def merge(self, other: "ValidationResult") -> None:
        """
        合并另一个验证结果

        Args:
            other: 另一个验证结果
        """
        if not other.is_valid:
            self.is_valid = False
        self.add_messages(other.messages)
        # 合并数据，other的数据优先
        if other.data:
            self.data.update(other.data)


class BaseValidator(ABC):
    """验证器基类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化验证器

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def validate(self, data: Any) -> ValidationResult:
        """
        验证数据

        Args:
            data: 要验证的数据

        Returns:
            验证结果
        """
        pass

    def validate_from_file(self, file_path: str) -> ValidationResult:
        """
        从文件验证数据

        Args:
            file_path: 文件路径

        Returns:
            验证结果
        """
        try:
            # 子类需要实现从文件读取数据的逻辑
            data = self._load_from_file(file_path)
            return self.validate(data)
        except Exception as e:
            self.logger.error(f"验证文件 {file_path} 失败: {str(e)}")
            return ValidationResult(False, messages=[f"验证文件失败: {str(e)}"])

    def _load_from_file(self, file_path: str) -> Any:
        """
        从文件加载数据

        Args:
            file_path: 文件路径

        Returns:
            加载的数据
        """
        raise NotImplementedError("子类必须实现_load_from_file方法")
