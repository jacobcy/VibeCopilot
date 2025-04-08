"""
测试验证器功能

用于测试新的验证器模块
"""

import logging
import sys
from pathlib import Path

from src.validation import ValidationResult, ValidatorFactory

# 设置日志级别
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_rule_validator():
    """测试规则验证器"""
    logger.info("测试规则验证器...")

    # 创建测试数据
    rule_data = {"id": "test_rule", "name": "测试规则", "type": "rule", "content": "# 测试规则\n\n这是一个测试规则", "description": "这是一个测试规则描述"}

    # 获取规则验证器
    validator = ValidatorFactory.get_validator("rule")

    # 验证数据
    result = validator.validate(rule_data)

    # 输出结果
    if result.is_valid:
        logger.info("规则验证通过")
    else:
        logger.error(f"规则验证失败: {', '.join(result.messages)}")

    # 验证缺少必填字段的数据
    incomplete_data = {"name": "不完整的规则", "type": "rule"}

    result = validator.validate(incomplete_data)

    if not result.is_valid:
        logger.info(f"预期的验证失败: {', '.join(result.messages)}")
    else:
        logger.error("验证应该失败但通过了")


def test_yaml_validator_with_file():
    """测试从文件验证YAML"""
    logger.info("测试从文件验证YAML...")

    # 创建测试YAML文件
    test_file = Path("test_rule.yaml")

    if test_file.exists():
        # 获取YAML验证器
        validator = ValidatorFactory.get_validator("yaml")

        # 验证文件
        result = validator.validate_from_file(str(test_file))

        # 输出结果
        if result.is_valid:
            logger.info(f"YAML文件验证通过: {test_file}")
            logger.info(f"解析数据: {result.data}")
        else:
            logger.error(f"YAML文件验证失败: {', '.join(result.messages)}")
    else:
        logger.error(f"测试文件不存在: {test_file}")


def main():
    """主函数"""
    logger.info("开始测试验证器模块...")

    # 测试规则验证器
    test_rule_validator()

    # 测试从文件验证YAML
    test_yaml_validator_with_file()

    logger.info("验证器测试完成")


if __name__ == "__main__":
    main()
