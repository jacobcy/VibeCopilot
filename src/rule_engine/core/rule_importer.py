"""
规则导入导出模块

提供规则导入和导出的功能
"""

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.models.rule_model import Rule
from src.parsing.processors.rule_processor import RuleProcessor
from src.rule_engine.exporters.rule_exporter import export_rule_to_yaml

logger = logging.getLogger(__name__)

# 创建规则处理器实例
rule_processor = RuleProcessor()


def import_rule_from_file(file_path: str, parser_type: Optional[str] = None, model: Optional[str] = None, validate: bool = True) -> Rule:
    """
    从文件导入规则（不含数据库操作）

    Args:
        file_path: 规则文件路径
        parser_type: 解析器类型
        model: 模型名称
        validate: 是否验证规则

    Returns:
        解析后的规则数据（Pydantic模型）
    """
    logger.info(f"从文件导入规则: {file_path}")

    # 使用规则处理器解析文件
    rule_dict = rule_processor.process_rule_file(file_path)

    # 将字典转换为Pydantic模型
    rule = Rule(**rule_dict)

    # 确保规则ID存在
    if not rule.id:
        path = Path(file_path)
        rule.id = path.stem
        rule_dict["id"] = rule.id

    # 确保规则名称存在
    if not rule.name:
        rule.name = rule.id
        rule_dict["name"] = rule.name

    # 确保规则类型存在
    if not rule.type:
        rule.type = "rule"
        rule_dict["type"] = rule.type

    # 确保规则描述存在
    if not rule.description:
        rule.description = f"从{Path(file_path).name}导入的规则"
        rule_dict["description"] = rule.description

    # 验证规则
    if validate and not rule_dict.get("validation", {}).get("valid", False):
        validation_errors = ", ".join(rule_dict.get("validation", {}).get("errors", []))
        logger.warning(f"规则验证警告: {validation_errors}")

    return rule


def import_rule_from_content(
    content: str, context: str = "", parser_type: Optional[str] = None, model: Optional[str] = None, validate: bool = True
) -> Rule:
    """
    从内容导入规则（不含数据库操作）

    Args:
        content: 规则内容
        context: 上下文信息
        parser_type: 解析器类型
        model: 模型名称
        validate: 是否验证规则

    Returns:
        解析后的规则数据（Pydantic模型）
    """
    logger.info(f"从内容导入规则, 上下文: {context}")

    # 使用规则处理器解析内容
    rule_dict = rule_processor.process_rule_text(content)

    # 将字典转换为Pydantic模型
    rule = Rule(**rule_dict)

    # 确保规则ID存在
    if not rule.id:
        rule.id = f"rule_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        rule_dict["id"] = rule.id

    # 确保规则名称存在
    if not rule.name:
        rule.name = rule.id
        rule_dict["name"] = rule.name

    # 确保规则类型存在
    if not rule.type:
        rule.type = "rule"
        rule_dict["type"] = rule.type

    # 确保规则描述存在
    if not rule.description:
        rule.description = "从内容导入的规则"
        rule_dict["description"] = rule.description

    # 验证规则
    if validate and not rule_dict.get("validation", {}).get("valid", False):
        validation_errors = ", ".join(rule_dict.get("validation", {}).get("errors", []))
        logger.warning(f"规则验证警告: {validation_errors}")

    return rule


def export_rule_to_format(rule: Rule, format_type: str = "yaml", output_path: Optional[str] = None) -> Union[str, Dict[str, Any]]:
    """
    导出规则到指定格式

    Args:
        rule: 规则对象
        format_type: 导出格式类型，支持yaml
        output_path: 输出路径

    Returns:
        根据format_type返回相应格式的规则数据
    """
    if format_type.lower() == "yaml":
        # 将规则导出为YAML格式
        yaml_content = export_rule_to_yaml(rule.dict())

        # 如果指定了输出路径，将内容写入文件
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(yaml_content)
                logger.info(f"规则已导出到: {output_path}")
            except Exception as e:
                logger.error(f"导出规则到文件时出错: {str(e)}")

        return yaml_content
    else:
        # 其他格式可以扩展
        logger.warning(f"不支持的导出格式: {format_type}")
        return rule.dict()
