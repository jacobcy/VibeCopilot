"""
规则验证器模块

提供规则验证功能，调用验证模块
"""

import logging
from typing import Any, Dict

from src.validation import ValidationResult, ValidatorFactory

logger = logging.getLogger(__name__)


def validate_rule(rule_data: Dict[str, Any]) -> ValidationResult:
    """验证规则数据

    Args:
        rule_data: 规则数据

    Returns:
        ValidationResult: 验证结果
    """
    logger.info(f"验证规则: {rule_data.get('id', 'unknown')}")

    # 使用验证器工厂获取规则验证器
    validator = ValidatorFactory.get_validator("rule")

    # 验证规则
    validation_result = validator.validate(rule_data)

    if validation_result.is_valid:
        logger.info(f"规则验证通过: {rule_data.get('id', 'unknown')}")
    else:
        validation_messages = ", ".join(validation_result.messages)
        logger.warning(f"规则验证未通过: {rule_data.get('id', 'unknown')}, 原因: {validation_messages}")

    return validation_result
