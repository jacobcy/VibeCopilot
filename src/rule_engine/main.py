#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
规则引擎主模块

提供规则引擎的主要功能和接口
"""

import logging
from typing import Any, Dict, Optional

from src.models.rule_model import Rule
from src.parsing.processors.rule_processor import RuleProcessor
from src.rule_engine.core.rule_importer import import_rule_from_content, import_rule_from_file
from src.rule_engine.core.rule_manager import RuleManager
from src.rule_engine.exporters.rule_exporter import export_rule_to_yaml
from src.rule_engine.generators.rule_generator import RuleGenerator, generate_rule_from_template
from src.validation.rule_validator import validate_rule

logger = logging.getLogger(__name__)

# 创建规则处理器实例
rule_processor = RuleProcessor()

# 导出公共API
__all__ = [
    "RuleManager",
    "Rule",
    "RuleProcessor",
    "init_rule_engine",
    "import_rule_from_file",
    "import_rule_from_content",
    "export_rule_to_yaml",
    "parse_rule_file",
    "parse_rule_content",
    "validate_rule",
    "RuleGenerator",
    "generate_rule_from_template",
]


def init_rule_engine(db_session=None) -> "RuleManager":
    """
    初始化规则引擎

    Args:
        db_session: 可选的数据库会话

    Returns:
        RuleManager实例
    """
    from src.rule_engine.core.rule_manager import RuleManager

    logger.info("初始化规则引擎")
    return RuleManager(db_session=db_session)


def generate_rule(template_id: str, variables: Dict[str, Any], rule_id: Optional[str] = None, use_llm: bool = False) -> Any:
    """
    基于模板生成规则的快捷方法

    Args:
        template_id: 模板ID
        variables: 模板变量
        rule_id: 规则ID，为空则自动生成
        use_llm: 是否使用LLM生成器

    Returns:
        规则对象，失败则返回None
    """
    return generate_rule_from_template(template_id, variables, rule_id, use_llm)


def get_rule_template(template_id: str) -> Optional[Dict[str, Any]]:
    """
    获取规则模板的快捷方法

    Args:
        template_id: 模板ID

    Returns:
        模板信息，包含id、path、content和metadata
    """
    generator = RuleGenerator()
    return generator.get_template(template_id)
