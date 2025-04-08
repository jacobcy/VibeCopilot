"""
规则验证器实现

提供对规则数据的验证功能
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from src.validation.core.yaml_validator import ValidationResult, YamlValidator

logger = logging.getLogger(__name__)


class RuleValidator(YamlValidator):
    """规则验证器，专门验证规则类数据"""

    def __init__(self, schema_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        初始化规则验证器

        Args:
            schema_path: 模式文件路径，不提供则使用默认模式
            config: 配置参数
        """
        # 如果没有提供模式路径，使用默认路径
        if not schema_path:
            # 相对于当前文件的路径
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            schema_path = os.path.join(current_dir, "schema", "rule_schema.yaml")

        super().__init__(schema_path, config)

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证规则数据

        Args:
            data: 要验证的规则数据

        Returns:
            验证结果
        """
        # 先进行基本验证
        result = super().validate(data)

        # 如果基本验证不通过，直接返回
        if not result.is_valid:
            return result

        # 规则特定验证
        if "id" not in data:
            result.is_valid = False
            result.add_message("规则必须包含id字段")

        if "name" not in data:
            result.is_valid = False
            result.add_message("规则必须包含name字段")

        if "type" not in data:
            # 自动修复：添加默认类型
            data["type"] = "rule"
            result.add_message("警告: 未指定规则类型，已设置为默认值'rule'")

        if "content" not in data:
            result.is_valid = False
            result.add_message("规则必须包含content字段")

        # 更新修复后的数据
        result.data = data

        return result
