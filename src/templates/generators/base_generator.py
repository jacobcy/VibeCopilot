"""
模板生成器基类

定义模板生成器的通用接口和基本功能。
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

from src.models import Template

logger = logging.getLogger(__name__)


class TemplateGenerator(ABC):
    """模板生成器基类"""

    @abstractmethod
    def generate(self, template: Template, variables: Dict[str, Any], output_format: str = "markdown") -> str:
        """
        生成内容

        Args:
            template: 模板对象
            variables: 变量值字典
            output_format: 输出格式，如markdown、json等

        Returns:
            生成的内容
        """
        pass

    @abstractmethod
    def validate_variables(self, template: Template, variables: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证变量值

        Args:
            template: 模板对象
            variables: 变量值字典

        Returns:
            (是否验证通过, 错误消息列表)
        """
        pass

    def prepare_variables(self, template: Template, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备并填充变量默认值

        Args:
            template: 模板对象
            variables: 变量值字典

        Returns:
            处理后的变量字典
        """
        prepared_variables = {}

        # 获取模板变量定义
        template_variables = template.variables if hasattr(template, "variables") else []

        # 填充默认值
        for var in template_variables:
            var_name = var.name
            if var_name in variables:
                # 用户提供的值
                prepared_variables[var_name] = variables[var_name]
            elif hasattr(var, "default") and var.default is not None:
                # 变量有默认值
                prepared_variables[var_name] = var.default
            elif getattr(var, "required", True):
                # 必需变量但未提供值，使用占位符
                prepared_variables[var_name] = f"[需要填写: {var_name}]"
            else:
                # 可选变量，使用空值
                prepared_variables[var_name] = ""

        # 添加任何其他用户提供的变量
        for key, value in variables.items():
            if key not in prepared_variables:
                prepared_variables[key] = value

        return prepared_variables
