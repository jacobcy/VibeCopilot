"""
规则生成器模块

根据模板生成规则文件。
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.template_engine import TemplateEngine
from ..models.rule import Rule, RuleMetadata, RuleType
from ..models.template import Template
from ..utils.template_utils import normalize_template_id

logger = logging.getLogger(__name__)


class RuleGenerator:
    """规则生成器类"""

    def __init__(self, template_engine: TemplateEngine):
        """
        初始化规则生成器

        Args:
            template_engine: 模板引擎
        """
        self.template_engine = template_engine

    def generate_rule(self, template: Template, variables: Dict[str, Any]) -> Rule:
        """
        根据模板生成规则对象

        Args:
            template: 模板对象
            variables: 变量值字典

        Returns:
            生成的规则对象
        """
        # 验证变量值
        errors = template.validate_variable_values(variables)
        if errors:
            error_messages = [f"{field}: {message}" for field, message in errors.items()]
            raise ValueError(f"变量验证失败: {'; '.join(error_messages)}")

        # 渲染模板内容
        rendered_content = self.template_engine.render_template(template, variables)

        # 从变量中提取规则属性
        rule_name = variables.get("title", template.name)
        rule_type_str = variables.get("type", template.type).upper()

        # 确保规则类型有效
        try:
            rule_type = RuleType(rule_type_str.lower())
        except ValueError:
            logger.warning(f"无效的规则类型 '{rule_type_str}'，使用默认类型 'agent'")
            rule_type = RuleType.AGENT

        # 创建规则元数据
        metadata = RuleMetadata(
            author=variables.get("author", template.metadata.author),
            tags=variables.get("tags", template.metadata.tags),
            version="1.0.0",
            dependencies=variables.get("dependencies", []),
        )

        # 创建规则对象
        rule = Rule(
            name=rule_name,
            type=rule_type,
            description=variables.get("description", ""),
            globs=variables.get("globs", []),
            always_apply=variables.get("always_apply", False),
            content=rendered_content,
            metadata=metadata,
        )

        # 设置规则ID
        rule.id = normalize_template_id(rule_name)

        return rule

    def generate_rule_file(
        self, template: Template, variables: Dict[str, Any], output_path: str
    ) -> Rule:
        """
        生成规则文件

        Args:
            template: 模板对象
            variables: 变量值字典
            output_path: 输出文件路径

        Returns:
            生成的规则对象
        """
        # 生成规则对象
        rule = self.generate_rule(template, variables)

        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rule.content)

        logger.info(f"规则文件已生成: {output_path}")

        return rule

    def generate_rule_json(self, rule: Rule, output_path: Optional[str] = None) -> str:
        """
        生成规则的JSON表示

        Args:
            rule: 规则对象
            output_path: 输出文件路径，如果提供则保存到文件

        Returns:
            JSON字符串
        """
        # 使用model_dump_json代替已弃用的json方法
        rule_json = rule.model_dump_json(exclude_none=True, indent=2)

        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rule_json)

            logger.info(f"规则JSON已生成: {output_path}")

        return rule_json

    def batch_generate_rules(
        self, template_configs: List[Dict[str, Any]], base_output_dir: str
    ) -> List[Rule]:
        """
        批量生成规则

        Args:
            template_configs: 模板配置列表，每项包含template、variables和output_file
            base_output_dir: 输出目录基路径

        Returns:
            生成的规则对象列表
        """
        generated_rules = []

        for config in template_configs:
            template = config.get("template")
            variables = config.get("variables", {})
            output_file = config.get("output_file")

            if not template or not output_file:
                logger.warning(f"跳过无效的模板配置: {config}")
                continue

            try:
                # 构建输出路径
                output_path = os.path.join(base_output_dir, output_file)

                # 生成规则文件
                rule = self.generate_rule_file(template, variables, output_path)
                generated_rules.append(rule)

            except Exception as e:
                logger.error(f"生成规则失败: {str(e)}")

        return generated_rules
