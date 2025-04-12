#!/usr/bin/env python3
"""
规则生成器模块

负责基于模板生成规则文件。
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from jinja2 import Template

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

# 配置日志
logger = logging.getLogger(__name__)


class RuleGenerator:
    """规则生成器类"""

    def __init__(self, template_repo=None, rule_repo=None):
        """初始化规则生成器

        Args:
            template_repo: 模板仓库实例，用于获取模板
            rule_repo: 规则仓库实例，用于存储生成的规则
        """
        self.template_repo = template_repo
        self.rule_repo = rule_repo

    def generate_rule(self, template_id: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """根据模板ID和变量生成规则数据

        Args:
            template_id: 模板ID或名称
            variables: 模板变量字典

        Returns:
            Dict[str, Any]: 生成的规则数据

        Raises:
            ValueError: 如果模板不存在或变量不足
        """
        logger.info(f"开始生成规则，使用模板: {template_id}")

        # 从数据库获取模板
        if self.template_repo:
            template = self.template_repo.get_template_by_id(template_id)
            if not template:
                # 尝试通过名称查找
                template = self.template_repo.get_template_by_name(template_id)

            if not template:
                raise ValueError(f"模板不存在: {template_id}")

            template_content = template.content
            template_variables = template.get_variables()

            # 检查必填变量
            missing_vars = []
            for var in template_variables:
                if var.required and var.name not in variables and not var.default_value:
                    missing_vars.append(var.name)

            if missing_vars:
                raise ValueError(f"缺少必填变量: {', '.join(missing_vars)}")

            # 应用默认值
            for var in template_variables:
                if var.name not in variables and var.default_value:
                    try:
                        variables[var.name] = json.loads(var.default_value)
                    except (json.JSONDecodeError, TypeError):
                        variables[var.name] = var.default_value
        else:
            # 从文件系统获取模板
            template_dirs = [Path("templates/rule"), Path.home() / "data/temp/templates/rule"]  # 项目规则模板目录  # 用户规则模板目录

            template_file = None
            for template_dir in template_dirs:
                if template_dir.exists():
                    # 尝试不同的扩展名
                    for ext in ["md", "markdown", "txt"]:
                        file_path = template_dir / f"{template_id}.{ext}"
                        if file_path.exists():
                            template_file = file_path
                            break

                    # 如果找到模板则停止查找
                    if template_file:
                        break

            if not template_file:
                raise ValueError(f"未找到模板文件: {template_id}")

            # 读取模板内容
            with open(template_file, "r", encoding="utf-8") as f:
                template_content = f.read()

        # 生成规则内容
        rule_content = self._render_template(template_content, variables)

        # 提取Front Matter (如果有)
        rule_data = self._extract_front_matter(rule_content)

        # 构建规则数据
        if not rule_data:
            rule_data = {}

        # 确保生成的规则有基本属性
        if "id" not in rule_data:
            rule_data["id"] = variables.get("id", f"rule_{datetime.now().strftime('%Y%m%d%H%M%S')}")

        if "type" not in rule_data:
            rule_data["type"] = variables.get("type", "rule")

        if "title" not in rule_data:
            rule_data["title"] = variables.get("title", rule_data["id"])

        if "content" not in rule_data:
            rule_data["content"] = rule_content

        logger.info(f"规则生成成功: {rule_data.get('id')}")
        return rule_data

    def generate_rule_file(self, template_id: str, variables: Dict[str, Any], output_path: Union[str, Path]) -> str:
        """根据模板生成规则文件

        Args:
            template_id: 模板ID或名称
            variables: 模板变量字典
            output_path: 输出文件路径

        Returns:
            str: 生成的文件路径

        Raises:
            ValueError: 如果模板不存在或变量不足
            IOError: 如果文件无法写入
        """
        # 生成规则内容
        rule_data = self.generate_rule(template_id, variables)
        rule_content = rule_data.get("content", "")

        # 将输出路径转换为Path对象
        if isinstance(output_path, str):
            output_path = Path(output_path)

        # 创建目标目录
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rule_content)
            logger.info(f"规则文件已保存到: {output_path}")
            return str(output_path)
        except IOError as e:
            logger.error(f"写入规则文件失败: {e}")
            raise IOError(f"无法写入规则文件: {e}")

    def save_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """保存规则数据到规则仓库

        Args:
            rule_data: 规则数据

        Returns:
            Dict[str, Any]: 保存后的规则数据

        Raises:
            RuntimeError: 如果规则仓库未设置
        """
        if not self.rule_repo:
            raise RuntimeError("规则仓库未设置，无法保存规则")

        # 确保规则有ID
        if "id" not in rule_data:
            rule_data["id"] = f"rule_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 保存到仓库
        return self.rule_repo.create(rule_data)

    def _render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """渲染模板内容

        Args:
            template_content: 模板内容
            variables: 变量字典

        Returns:
            str: 渲染后的内容
        """
        logger.debug(f"渲染模板，变量: {list(variables.keys())}")

        # 尝试使用Jinja2，如果不可用则使用简单替换
        if JINJA2_AVAILABLE:
            try:
                template = Template(template_content)
                return template.render(**variables)
            except Exception as e:
                logger.warning(f"Jinja2渲染失败，回退到简单替换: {e}")

        # 简单替换 {{变量}} 格式的模板变量
        result = template_content
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))

        return result

    def _extract_front_matter(self, content: str) -> Optional[Dict[str, Any]]:
        """从内容中提取Front Matter

        Args:
            content: 含有Front Matter的内容

        Returns:
            Optional[Dict[str, Any]]: 提取的Front Matter数据，如果未找到则返回None
        """
        # 检查是否包含Front Matter (三个连字符分割)
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        # 提取中间部分
        front_matter_str = parts[1].strip()
        if not front_matter_str:
            return None

        # 尝试作为YAML解析
        try:
            import yaml

            return yaml.safe_load(front_matter_str)
        except (ImportError, yaml.YAMLError):
            # YAML解析失败或库不可用，使用简单解析
            result = {}
            for line in front_matter_str.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # 尝试按冒号分割
                key_value = line.split(":", 1)
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip()
                    result[key] = value

            return result


def generate_rule_from_template(template_id: str, variables: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
    """基于模板生成规则

    Args:
        template_id: 模板ID或名称
        variables: 模板变量字典
        output_path: 可选的输出文件路径

    Returns:
        Dict[str, Any]: 生成的规则数据
    """
    generator = RuleGenerator()
    rule_data = generator.generate_rule(template_id, variables)

    if output_path:
        generator.generate_rule_file(template_id, variables, output_path)

    return rule_data
