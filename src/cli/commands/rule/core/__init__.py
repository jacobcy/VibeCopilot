"""
规则命令核心模块

包含规则命令的核心功能模块。
"""

from src.cli.commands.rule.core.arg_parser import parse_rule_args
from src.cli.commands.rule.core.command_executor import RuleCommandExecutor

__all__ = ["parse_rule_args", "RuleCommandExecutor"]
