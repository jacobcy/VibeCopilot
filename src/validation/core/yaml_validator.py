"""
YAML验证器模块

提供YAML文件的验证和自动修复功能
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

from src.validation.core.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class YamlValidator(BaseValidator):
    """YAML验证器基类，提供基本的YAML验证功能"""

    def __init__(self, schema_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        初始化YAML验证器

        Args:
            schema_path: 模式文件路径
            config: 配置参数
        """
        super().__init__(config)
        self.schema_path = schema_path
        self.schema = None

        if schema_path and os.path.exists(schema_path):
            self._load_schema()

    def _load_schema(self) -> None:
        """加载模式文件"""
        try:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                self.schema = yaml.safe_load(f)
            self.logger.info(f"已加载模式文件: {self.schema_path}")
        except Exception as e:
            self.logger.error(f"加载模式文件 {self.schema_path} 失败: {str(e)}")
            self.schema = None

    def _load_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        从YAML文件加载数据

        Args:
            file_path: YAML文件路径

        Returns:
            加载的数据
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data
        except Exception as e:
            self.logger.error(f"加载YAML文件 {file_path} 失败: {str(e)}")
            raise

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证YAML数据

        Args:
            data: 要验证的YAML数据

        Returns:
            验证结果
        """
        # 基本验证，子类应该重写此方法
        result = ValidationResult(True, data=data)

        # 检查数据类型
        if not isinstance(data, dict):
            result.is_valid = False
            result.add_message("数据必须是字典类型")
            return result

        # 如果有模式，进行模式验证
        if self.schema:
            # 子类实现模式验证逻辑
            schema_result = self._validate_against_schema(data)
            result.merge(schema_result)

        return result

    def _validate_against_schema(self, data: Dict[str, Any]) -> ValidationResult:
        """
        根据模式验证数据

        Args:
            data: 要验证的数据

        Returns:
            验证结果
        """
        # 基本实现，子类应重写此方法进行更详细的验证
        result = ValidationResult(True, data=data)

        if not self.schema:
            return result

        # 这里应该实现具体的模式验证逻辑
        # 例如检查必填字段、类型验证等

        return result

    def generate_fixed_yaml(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        生成修复后的YAML文件

        Args:
            data: 修复后的数据
            output_path: 输出文件路径

        Returns:
            bool: 是否成功生成
        """
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            self.logger.info(f"已生成修复后的YAML文件: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"生成修复后的YAML文件 {output_path} 失败: {str(e)}")
            return False

    def validate_from_file(self, file_path: str) -> ValidationResult:
        """
        从文件验证YAML数据

        Args:
            file_path: YAML文件路径

        Returns:
            验证结果
        """
        try:
            data = self._load_from_file(file_path)
            return self.validate(data)
        except Exception as e:
            self.logger.error(f"验证YAML文件 {file_path} 失败: {str(e)}")
            return ValidationResult(False, messages=[f"验证YAML文件失败: {str(e)}"])
