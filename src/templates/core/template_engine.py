"""
模板引擎核心模块

提供模板渲染、变量替换和应用等核心功能。
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jinja2 import Environment, FileSystemLoader
from jinja2 import Template as JinjaTemplate
from jinja2 import select_autoescape

from ..models.template import Template, TemplateVariable
from .managers.template_utils import get_syntax_error_details, validate_template_syntax

logger = logging.getLogger(__name__)


class TemplateEngine:
    """模板引擎核心类"""

    def __init__(self, templates_dir: Optional[str] = None):
        """
        初始化模板引擎

        Args:
            templates_dir: 模板目录路径，如果提供则自动加载该目录下的模板
        """
        self.env = Environment(
            loader=FileSystemLoader(templates_dir) if templates_dir else None,
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.templates_dir = templates_dir
        self._setup_custom_filters()

    def _setup_custom_filters(self):
        """设置自定义模板过滤器"""
        # 添加驼峰命名转换过滤器
        self.env.filters["camel_case"] = lambda s: "".join(word.capitalize() if i else word.lower() for i, word in enumerate(s.split("_")))
        # 添加帕斯卡命名转换过滤器
        self.env.filters["pascal_case"] = lambda s: "".join(word.capitalize() for word in s.split("_"))
        # 添加kebab命名转换过滤器
        self.env.filters["kebab_case"] = lambda s: "-".join(word.lower() for word in s.split("_"))

    def render_template_string(self, template_string: str, variables: Dict[str, Any]) -> str:
        """
        渲染模板字符串

        Args:
            template_string: 模板内容字符串
            variables: 变量值字典

        Returns:
            渲染后的内容
        """
        if not validate_template_syntax(template_string):
            error_details = get_syntax_error_details(template_string)
            raise ValueError(f"模板语法错误: {error_details['message']} at line {error_details['line']}")

        template = self.env.from_string(template_string)
        return template.render(**variables)

    def render_template(self, template: Template, variables: Dict[str, Any]) -> str:
        """
        渲染模板

        Args:
            template: 模板对象
            variables: 变量值字典

        Returns:
            渲染后的内容
        """
        # 验证变量值
        errors = template.validate_variable_values(variables)
        if errors:
            error_messages = [f"{field}: {message}" for field, message in errors.items()]
            raise ValueError(f"变量验证失败: {'; '.join(error_messages)}")

        # 添加默认值
        variables_with_defaults = variables.copy()
        for var in template.variables:
            if var.name not in variables_with_defaults and var.default is not None:
                variables_with_defaults[var.name] = var.default

        return self.render_template_string(template.content, variables_with_defaults)

    def apply_template(self, template: Template, variables: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        应用模板并可选地保存到文件

        Args:
            template: 模板对象
            variables: 变量值字典
            output_path: 输出文件路径，如果提供则保存到文件

        Returns:
            渲染后的内容
        """
        rendered_content = self.render_template(template, variables)

        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered_content)

            logger.info(f"模板已应用并保存到: {output_path}")

        return rendered_content

    def load_template_from_file(self, file_path: str) -> JinjaTemplate:
        """
        从文件加载Jinja模板

        Args:
            file_path: 模板文件路径，相对于模板目录

        Returns:
            Jinja模板对象
        """
        return self.env.get_template(file_path)

    def get_template_variables(self, template: Template) -> List[TemplateVariable]:
        """
        获取模板的变量列表

        Args:
            template: 模板对象

        Returns:
            变量列表
        """
        return template.variables
