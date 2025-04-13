"""
模板工具函数模块

提供模板处理相关的辅助函数，如变量提取、内容验证等。
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from jinja2 import Environment, exceptions, meta

logger = logging.getLogger(__name__)


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


def preprocess_jinja2_variables(content: str) -> Tuple[str, Dict[str, str]]:
    """
    预处理Jinja2变量，将模板变量替换为YAML安全的占位符

    Args:
        content: 包含可能有Jinja2变量的内容

    Returns:
        Tuple[str, Dict[str, str]]: 处理后的内容和占位符映射
    """
    # 提取Jinja2变量并替换为占位符
    placeholders = {}
    pattern = r"{{(.*?)}}"

    def replace_vars(match):
        var_content = match.group(0)  # 完整匹配，包括{{和}}
        placeholder = f"__JINJA2_VAR_{len(placeholders)}__"
        placeholders[placeholder] = var_content
        return placeholder

    processed_content = re.sub(pattern, replace_vars, content)

    return processed_content, placeholders


def restore_jinja2_variables(content: str, placeholders: Dict[str, str]) -> str:
    """
    还原被替换的Jinja2变量

    Args:
        content: 包含占位符的内容
        placeholders: 占位符到原始变量的映射

    Returns:
        还原后的内容
    """
    result = content
    for placeholder, original in placeholders.items():
        result = result.replace(placeholder, original)
    return result


def parse_template_with_llm(content: str, file_path: str = None) -> Dict[str, Any]:
    """
    使用LLM解析模板内容，特别是在传统解析器失败的情况下

    Args:
        content: 模板内容
        file_path: 可选的文件路径，用于提供上下文

    Returns:
        解析后的模板数据
    """
    try:
        # 导入解析模块，如果不可用则提前返回
        try:
            from src.parsing.llm_parser import LLMParser
            from src.parsing.parser_factory import get_parser_instance
        except ImportError:
            logger.warning("无法导入LLM解析器，跳过LLM解析")
            return None

        # 获取LLM解析器实例
        try:
            llm_parser = get_parser_instance("llm")
        except Exception as e:
            logger.warning(f"无法获取LLM解析器实例: {str(e)}")
            # 尝试直接创建
            llm_parser = LLMParser()

        # 准备文件上下文
        template_name = Path(file_path).stem if file_path else "未知模板"
        context = {"file_name": template_name, "file_path": file_path, "parse_mode": "template", "content_type": "template"}

        # 使用LLM解析
        result = llm_parser.parse_file(file_path) if file_path else llm_parser.parse_text(content, context)

        # 检查解析结果
        if not result or not result.get("success", False):
            logger.warning(f"LLM解析失败: {result.get('error', '未知错误')}")
            return None

        # 提取元数据和内容
        metadata = result.get("metadata", {})
        parsed_content = result.get("content", content)

        # 构建标准模板数据结构
        template_data = {
            "name": metadata.get("title", template_name),
            "description": metadata.get("description", ""),
            "type": metadata.get("type", "doc"),
            "content": parsed_content,
            "metadata": {
                "author": metadata.get("author", ""),
                "tags": metadata.get("tags", []),
                "version": metadata.get("version", "1.0.0"),
            },
        }
        logger.info(f"成功使用LLM解析模板: {template_name}")
        return template_data

    except Exception as e:
        logger.error(f"使用LLM解析模板时出错: {str(e)}")
        return None


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
    original_content = content
    yaml_parse_failed = False

    if content.startswith("---"):
        try:
            # 找到第二个'---'的位置
            end_marker = content.find("---", 3)
            if end_marker != -1:
                yaml_str = content[3:end_marker].strip()

                # 预处理Jinja2变量，避免YAML解析错误
                processed_yaml_str, placeholders = preprocess_jinja2_variables(yaml_str)

                # 解析YAML
                yaml_data = yaml.safe_load(processed_yaml_str)

                # 还原任何被处理的键值中的Jinja2变量
                if yaml_data and isinstance(yaml_data, dict):
                    for key, value in yaml_data.items():
                        if isinstance(value, str) and any(p in value for p in placeholders.keys()):
                            yaml_data[key] = restore_jinja2_variables(value, placeholders)

                # 去除前置元数据部分，只保留正文内容
                content = content[end_marker + 3 :].strip()
        except yaml.YAMLError as e:
            logger.error(f"YAML解析错误: {str(e)}")
            yaml_parse_failed = True

            # 先尝试使用文件名作为备用标题
            yaml_data = {"title": path.stem}

            # 确保保留完整内容以防解析失败
            if end_marker != -1:
                content = content[end_marker + 3 :].strip()

    # 如果YAML解析失败，尝试使用LLM解析
    if yaml_parse_failed:
        logger.info(f"尝试使用LLM解析模板: {path.name}")
        llm_parsed = parse_template_with_llm(original_content, file_path)

        if llm_parsed:
            return llm_parsed

    # 构建并返回模板数据
    return {
        "name": yaml_data.get("title", path.stem),
        "description": yaml_data.get("description", ""),
        "type": yaml_data.get("type", "doc"),
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
