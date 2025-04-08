"""
基于正则表达式的模板生成器

使用本地正则表达式替换实现模板生成，适用于简单场景和离线环境。
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import jinja2
from jinja2 import Environment
from jinja2 import Template as Jinja2Template
from jinja2.exceptions import TemplateSyntaxError, UndefinedError

from src.models import Template

from .base_generator import TemplateGenerator

logger = logging.getLogger(__name__)


class RegexTemplateGenerator(TemplateGenerator):
    """基于正则表达式的模板生成器"""

    def __init__(self, strict_mode: bool = False):
        """
        初始化正则表达式模板生成器

        Args:
            strict_mode: 严格模式，如果为True，则缺少变量会导致生成失败
        """
        self.strict_mode = strict_mode
        # 配置Jinja2环境
        self.env = Environment(
            keep_trailing_newline=True,  # 保留末尾换行符
            trim_blocks=True,  # 移除块级标签后的第一个换行
            lstrip_blocks=True,  # 移除块级标签前的空格
        )
        # 添加自定义过滤器
        self._add_custom_filters()

    def _add_custom_filters(self) -> None:
        """添加自定义过滤器"""

        # 添加JSON处理过滤器
        def json_filter(value, indent=2):
            return json.dumps(value, ensure_ascii=False, indent=indent)

        self.env.filters["json"] = json_filter

        # 添加默认值过滤器
        def default_filter(value, default_value=""):
            return value if value is not None else default_value

        self.env.filters["default"] = default_filter

        # 添加数组处理过滤器
        def join_filter(value, delimiter=", "):
            if isinstance(value, list):
                return delimiter.join(str(item) for item in value)
            return str(value)

        self.env.filters["join"] = join_filter

    def prepare_variables(self, template: Template, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备变量，确保所有需要的变量都有值

        Args:
            template: 模板对象
            variables: 用户提供的变量

        Returns:
            处理后的变量字典
        """
        result = {}

        # 复制用户提供的变量
        result.update(variables)

        # 获取模板变量定义
        template_variables = template.variables if hasattr(template, "variables") else []

        # 为没有提供的变量设置默认值
        for var in template_variables:
            var_name = var.name

            # 如果变量未提供，使用默认值
            if var_name not in result:
                default_value = getattr(var, "default", None)
                if default_value is not None:
                    result[var_name] = default_value
                elif not getattr(var, "required", True):
                    # 非必须变量设置为空字符串或空列表
                    var_type = getattr(var, "type", "string")
                    if var_type == "array":
                        result[var_name] = []
                    elif var_type == "object":
                        result[var_name] = {}
                    elif var_type == "boolean":
                        result[var_name] = False
                    elif var_type == "number":
                        result[var_name] = 0
                    else:
                        result[var_name] = ""

        # 特殊处理某些复杂类型
        # 例如确保parameters在命令模板中正确处理
        if "parameters" in result and isinstance(result["parameters"], list):
            # 确保每个参数对象都有required字段，默认为True
            for param in result["parameters"]:
                if isinstance(param, dict) and "required" not in param:
                    param["required"] = True

        return result

    def generate(self, template: Template, variables: Dict[str, Any], output_format: str = "markdown") -> str:
        """
        使用正则表达式生成内容

        Args:
            template: 模板对象
            variables: 变量值字典
            output_format: 输出格式

        Returns:
            生成的内容
        """
        # 验证变量
        valid, errors = self.validate_variables(template, variables)
        if not valid and self.strict_mode:
            error_msg = "; ".join(errors)
            raise ValueError(f"变量验证失败: {error_msg}")

        # 记录输入变量（调试用）
        logger.debug(f"模板：{template.id}, 输入变量: {json.dumps(variables, ensure_ascii=False)}")

        # 准备变量
        prepared_variables = self.prepare_variables(template, variables)

        # 记录处理后变量（调试用）
        logger.debug(f"处理后变量: {json.dumps(prepared_variables, ensure_ascii=False)}")

        # 预处理特定类型的模板
        template_content = template.content

        # 尝试处理命令模板中的参数列表
        if template.id == "template_956c81b4" and "parameters" in prepared_variables:
            # 确保参数列表循环语句正确
            template_content = self._fix_command_template(template_content)

        try:
            # 编译Jinja2模板
            jinja_template = self.env.from_string(template_content)

            # 渲染模板
            content = jinja_template.render(**prepared_variables)

            # 根据输出格式处理
            if output_format == "json":
                # 如果需要JSON输出，可以在这里处理
                # 这里暂时简单返回
                return content
            else:
                # 默认Markdown格式
                return content

        except TemplateSyntaxError as e:
            logger.error(f"模板语法错误: {str(e)}")
            raise ValueError(f"模板语法错误: {str(e)}")
        except UndefinedError as e:
            logger.error(f"模板变量未定义: {str(e)}")
            if self.strict_mode:
                raise ValueError(f"模板变量未定义: {str(e)}")
            # 非严格模式下尽可能生成
            # 尝试使用简单字符串替换
            return self._fallback_generate(template, prepared_variables)
        except Exception as e:
            logger.error(f"模板生成错误: {str(e)}")
            raise ValueError(f"模板生成错误: {str(e)}")

    def _fix_command_template(self, content: str) -> str:
        """
        修复命令模板中的常见问题

        Args:
            content: 原始模板内容

        Returns:
            修复后的模板内容
        """
        # 修复参数列表循环的格式问题
        fixed_content = content.replace(
            "{% for param in parameters %}\n- `{{param.name}}`: {{param.description}}{% if param.required %} (必填){% endif %}\n{% endfor %}",
            "{% for param in parameters %}\n- `{{param.name}}`: {{param.description}}{% if param.required %} (必填){% endif %}\n{% endfor %}",
        )

        # 可以添加其他格式修复

        return fixed_content

    def _fallback_generate(self, template: Template, variables: Dict[str, Any]) -> str:
        """
        备用生成方法，使用简单字符串替换

        Args:
            template: 模板对象
            variables: 变量值字典

        Returns:
            生成的内容
        """
        logger.warning("使用备用生成方法")
        content = template.content

        # 简单变量替换
        for key, value in variables.items():
            # 对不同类型的值进行处理
            if isinstance(value, (dict, list)):
                # 复杂类型转为JSON字符串
                str_value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, bool):
                # 布尔值转为"true"/"false"
                str_value = str(value).lower()
            else:
                # 其他类型转为字符串
                str_value = str(value)

            # 替换模板中的变量
            pattern = r"\{\{\s*" + re.escape(key) + r"\s*\}\}"
            content = re.sub(pattern, str_value, content)

        # 特殊处理循环和条件
        # 这里简单处理命令模板中的参数列表
        if "parameters" in variables and isinstance(variables["parameters"], list):
            params_list = ""
            for param in variables["parameters"]:
                if isinstance(param, dict):
                    param_name = param.get("name", "")
                    param_desc = param.get("description", "")
                    required = param.get("required", True)
                    required_text = " (必填)" if required else ""
                    params_list += f"- `{param_name}`: {param_desc}{required_text}\n"

            # 替换参数列表
            pattern = r"\{%\s*for\s+param\s+in\s+parameters\s*%\}.*?\{%\s*endfor\s*%\}"
            content = re.sub(pattern, params_list, content, flags=re.DOTALL)

        return content

    def validate_variables(self, template: Template, variables: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证变量值

        Args:
            template: 模板对象
            variables: 变量值字典

        Returns:
            (是否验证通过, 错误消息列表)
        """
        errors = []

        # 获取模板变量定义
        template_variables = template.variables if hasattr(template, "variables") else []

        # 检查必需变量
        for var in template_variables:
            var_name = var.name
            is_required = getattr(var, "required", True)

            if is_required and var_name not in variables:
                errors.append(f"缺少必需变量: {var_name}")

        # 检查变量类型（简单验证）
        for var in template_variables:
            var_name = var.name
            var_type = getattr(var, "type", None)

            if var_name in variables and var_type:
                value = variables[var_name]

                # 简单类型检查
                if var_type == "string" and not isinstance(value, str):
                    errors.append(f"变量 {var_name} 应为字符串类型")
                elif var_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"变量 {var_name} 应为数字类型")
                elif var_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"变量 {var_name} 应为布尔类型")
                elif var_type == "array" and not isinstance(value, list):
                    errors.append(f"变量 {var_name} 应为数组类型")
                elif var_type == "object" and not isinstance(value, dict):
                    errors.append(f"变量 {var_name} 应为对象类型")

        return len(errors) == 0, errors
