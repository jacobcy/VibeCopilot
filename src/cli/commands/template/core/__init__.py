"""
模板命令核心模块

包含模板命令的核心功能模块。
"""

from src.cli.commands.template.core.advanced_executor import TemplateAdvancedExecutor
from src.cli.commands.template.core.arg_parser import parse_template_args
from src.cli.commands.template.core.command_executor import TemplateCommandExecutor

__all__ = ["parse_template_args", "TemplateCommandExecutor", "TemplateAdvancedExecutor"]
