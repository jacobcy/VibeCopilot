"""
模板工具函数模块

提供模板处理相关的辅助函数，如变量提取、内容验证等。
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml
from jinja2 import Environment, exceptions, meta


def extract_variables_from_template(template_content: str) -> Set[str]:
    """
    从模板内容中提取变量

    Args:
        template_content: 模板内容字符串

    Returns:
        变量名集合
    """
    env = Environment()
    try:
        ast = env.parse(template_content)
        variables = meta.find_undeclared_variables(ast)
        return variables
    except exceptions.TemplateSyntaxError as e:
        raise ValueError(f"模板语法错误: {str(e)}")


def validate_template_syntax(template_content: str) -> bool:
    """
    验证模板语法是否正确

    Args:
        template_content: 模板内容字符串

    Returns:
        语法是否正确
    """
    env = Environment()
    try:
        env.parse(template_content)
        return True
    except exceptions.TemplateSyntaxError:
        return False


def get_syntax_error_details(template_content: str) -> Optional[Dict[str, Any]]:
    """
    获取模板语法错误详情

    Args:
        template_content: 模板内容字符串

    Returns:
        错误详情，如果没有错误则返回None
    """
    env = Environment()
    try:
        env.parse(template_content)
        return None
    except exceptions.TemplateSyntaxError as e:
        return {
            "line": e.lineno,
            "message": str(e),
            "source": e.source.splitlines()[e.lineno - 1] if e.source else None,
        }


def load_template_from_file(file_path: str) -> Dict[str, Any]:
    """
    从文件加载模板

    Args:
        file_path: 模板文件路径

    Returns:
        模板数据字典
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"模板文件不存在: {file_path}")

    content = path.read_text(encoding="utf-8")

    # 提取前置YAML元数据
    yaml_data = {}
    if content.startswith("---"):
        try:
            # 找到第二个'---'的位置
            end_marker = content.find("---", 3)
            if end_marker != -1:
                yaml_str = content[3:end_marker].strip()
                yaml_data = yaml.safe_load(yaml_str)
                content = content[end_marker + 3 :].strip()
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析错误: {str(e)}")

    return {
        "name": yaml_data.get("title", path.stem),
        "description": yaml_data.get("description", ""),
        "type": yaml_data.get("type", "agent"),
        "content": content,
        "metadata": {
            "author": yaml_data.get("author", ""),
            "tags": yaml_data.get("tags", []),
            "version": yaml_data.get("version", "1.0.0"),
        },
    }


def normalize_template_id(name: str) -> str:
    """
    将模板名称标准化为ID

    Args:
        name: 模板名称

    Returns:
        标准化的模板ID
    """
    # 移除特殊字符，将空格转为连字符
    normalized = re.sub(r"[^\w\s-]", "", name.lower())
    normalized = re.sub(r"[\s]+", "-", normalized)
    return normalized
