#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则引擎模块

提供规则解析、执行和管理功能
"""

import logging

from src.models.rule_model import Example, Rule, RuleItem, RuleMetadata
from src.rule_engine.main import (
    RuleGenerator,
    export_rule_to_yaml,
    generate_rule,
    generate_rule_from_template,
    get_rule_template,
    init_rule_engine,
    validate_rule,
)
from src.rule_engine.rule_manager import RuleManager

logger = logging.getLogger(__name__)

# 导出主要类和函数
__all__ = [
    "Rule",
    "RuleItem",
    "Example",
    "RuleMetadata",
    "RuleManager",
    "export_rule_to_yaml",
    "validate_rule",
    "RuleGenerator",
    "generate_rule_from_template",
    "init_rule_engine",
    "generate_rule",
    "get_rule_template",
]
