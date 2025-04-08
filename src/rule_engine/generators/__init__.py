#!/usr/bin/env python3
"""
规则生成器模块

负责基于模板生成规则文件。
"""

from src.rule_engine.generators.rule_generator import RuleGenerator, generate_rule_from_template

__all__ = ["RuleGenerator", "generate_rule_from_template"]
