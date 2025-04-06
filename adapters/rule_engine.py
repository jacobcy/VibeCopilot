"""
规则引擎接口模块
提供统一的规则引擎接口，使用content_parser解析规则文件
"""

import logging
import os
from typing import Any, Dict, List, Optional

from adapters.content_parser import parse_content, parse_file

logger = logging.getLogger(__name__)


def parse_rule_file(
    file_path: str, parser_type: Optional[str] = None, model: Optional[str] = None
) -> Dict[str, Any]:
    """解析规则文件

    使用统一的content_parser接口解析规则文件

    Args:
        file_path: 规则文件路径
        parser_type: 解析器类型，如不指定则使用默认值
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        Dict: 解析后的规则结构
    """
    logger.info(f"使用content_parser解析规则文件: {file_path}")

    # 调用统一的内容解析接口
    result = parse_file(
        file_path=file_path, content_type="rule", parser_type=parser_type, model=model
    )

    logger.info(f"规则文件解析完成: {file_path}")
    return result


def parse_rule_content(
    content: str, context: str = "", parser_type: Optional[str] = None, model: Optional[str] = None
) -> Dict[str, Any]:
    """解析规则内容

    使用统一的content_parser接口解析规则内容

    Args:
        content: 规则文本内容
        context: 上下文信息(文件路径等)
        parser_type: 解析器类型，如不指定则使用默认值
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        Dict: 解析后的规则结构
    """
    logger.info(f"使用content_parser解析规则内容, 上下文: {context}")

    # 调用统一的内容解析接口
    result = parse_content(
        content=content, context=context, content_type="rule", parser_type=parser_type, model=model
    )

    logger.info(f"规则内容解析完成")
    return result


def detect_rule_conflicts(
    rule_a: Dict[str, Any], rule_b: Dict[str, Any], parser_type: Optional[str] = None
) -> Dict[str, Any]:
    """检测两个规则之间的冲突

    Args:
        rule_a: 第一个规则
        rule_b: 第二个规则
        parser_type: 解析器类型

    Returns:
        Dict: 冲突分析结果
    """
    logger.info(f"检测规则冲突: {rule_a.get('id', 'unknown')} 与 {rule_b.get('id', 'unknown')}")

    # 简单的规则冲突检查
    # 检查基本冲突：相同ID但内容不同
    if rule_a.get("id") == rule_b.get("id") and rule_a.get("content") != rule_b.get("content"):
        logger.info(f"检测到ID冲突: {rule_a.get('id')}")
        return {
            "has_conflict": True,
            "conflict_type": "duplicate_id",
            "conflict_description": f"规则ID '{rule_a.get('id')}' 相同但内容不同",
        }

    # 检查globs冲突
    a_globs = set(rule_a.get("globs", []))
    b_globs = set(rule_b.get("globs", []))

    if a_globs and b_globs and a_globs.intersection(b_globs):
        intersection = a_globs.intersection(b_globs)
        logger.info(f"检测到glob模式重叠: {intersection}")
        return {
            "has_conflict": True,
            "conflict_type": "glob_overlap",
            "conflict_description": f"规则glob模式重叠: {intersection}",
        }

    # 未检测到简单冲突
    logger.info("简单检查未发现冲突")
    return {"has_conflict": False, "conflict_type": "none", "conflict_description": "简单检查未发现冲突"}
