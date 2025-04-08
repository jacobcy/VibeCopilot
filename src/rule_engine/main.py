"""
规则引擎入口模块

作为规则引擎的入口，导出主要功能
"""

import logging
from typing import Any, Dict, Optional

from src.rule_engine.core.rule_manager import RuleManager
from src.rule_engine.exporters.rule_exporter import export_rule_to_yaml
from src.rule_engine.generators.rule_generator import RuleGenerator, generate_rule_from_template
from src.rule_engine.parsers.rule_parser import parse_rule_content, parse_rule_file
from src.rule_engine.validators.rule_validator import validate_rule

logger = logging.getLogger(__name__)

# 导出公共API
__all__ = [
    "init_rule_engine",
    "RuleManager",
    "parse_rule_file",
    "parse_rule_content",
    "export_rule_to_yaml",
    "validate_rule",
    "RuleGenerator",
    "generate_rule_from_template",
]


def init_rule_engine() -> RuleManager:
    """
    初始化规则引擎

    Returns:
        RuleManager: 初始化后的规则管理器实例
    """
    return RuleManager()


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
