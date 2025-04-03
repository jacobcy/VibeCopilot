"""
数据库工具函数

提供数据库操作相关的工具函数，包括ID生成、Markdown解析等。
"""

import hashlib
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import yaml
from sqlalchemy.orm import Session


def generate_id(prefix: str, name: str) -> str:
    """
    生成唯一ID

    基于前缀和名称生成短而唯一的ID

    Args:
        prefix: ID前缀 (E=Epic, S=Story, T=Task, L=Label)
        name: 实体名称

    Returns:
        格式化的ID
    """
    # 使用名称的哈希值生成唯一性标识符
    name_hash = hashlib.md5(name.encode("utf-8")).hexdigest()[:4]
    timestamp = int(datetime.now().timestamp())
    unique_part = f"{timestamp % 10000:04d}"

    return f"{prefix}{unique_part}"


def standardize_id(entity_type: str, input_id: str) -> str:
    """
    标准化ID格式

    确保ID符合系统要求的格式 (前缀+数字)

    Args:
        entity_type: 实体类型 ('epic', 'story', 'task', 'label')
        input_id: 输入的ID

    Returns:
        标准化后的ID
    """
    # 类型前缀映射
    prefixes = {"epic": "E", "story": "S", "task": "T", "label": "L"}

    # 确保类型有效
    if entity_type.lower() not in prefixes:
        raise ValueError(f"无效的实体类型: {entity_type}")

    prefix = prefixes[entity_type.lower()]

    # 检查是否已经是标准格式 (前缀+数字)
    pattern = re.compile(f"^{prefix}\\d+$")
    if pattern.match(input_id):
        return input_id

    # 提取数字部分 (如果有)
    numeric_parts = re.findall(r"\d+", input_id)
    if numeric_parts:
        # 使用最后一个数字部分
        return f"{prefix}{numeric_parts[-1]:0>4}"

    # 如果没有数字部分，生成一个随机数字
    return f"{prefix}{uuid.uuid4().int % 10000:04d}"


def parse_markdown_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    解析Markdown前置元数据

    从Markdown内容中提取YAML前置元数据和正文

    Args:
        content: Markdown内容

    Returns:
        元组 (前置元数据字典, Markdown正文)
    """
    # 查找前置元数据 (---YAML---)
    frontmatter_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    frontmatter_match = frontmatter_pattern.search(content)

    if frontmatter_match:
        # 提取元数据和正文
        frontmatter_yaml = frontmatter_match.group(1)
        body = content[frontmatter_match.end() :]

        try:
            # 解析YAML
            metadata = yaml.safe_load(frontmatter_yaml)
            if not isinstance(metadata, dict):
                metadata = {}
        except yaml.YAMLError:
            # 解析失败时返回空字典
            metadata = {}
    else:
        # 没有找到前置元数据
        metadata = {}
        body = content

    return metadata, body


def create_markdown_with_frontmatter(metadata: Dict[str, Any], body: str) -> str:
    """
    创建带前置元数据的Markdown

    将元数据和正文组合成Markdown格式

    Args:
        metadata: 元数据字典
        body: Markdown正文

    Returns:
        完整的Markdown内容
    """
    # 将元数据转换为YAML
    frontmatter = yaml.dump(metadata, allow_unicode=True, sort_keys=False)

    # 组合成Markdown
    return f"---\n{frontmatter}---\n\n{body}"


def extract_id_from_filename(filename: str) -> Optional[str]:
    """
    从文件名中提取ID

    Args:
        filename: 文件名 (如 "T1001-任务名称.md")

    Returns:
        提取的ID或None
    """
    # 匹配常见ID格式 (如E1001, S1001, T1001)
    id_pattern = re.compile(r"^([EST]\d+)")
    match = id_pattern.search(filename)

    if match:
        return match.group(1)

    return None


def format_date(date_obj: Optional[datetime] = None) -> str:
    """
    格式化日期

    Args:
        date_obj: 日期对象 (默认为当前时间)

    Returns:
        格式化的日期字符串 (YYYY-MM-DD)
    """
    if date_obj is None:
        date_obj = datetime.now()

    return date_obj.strftime("%Y-%m-%d")


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全获取字典中的值

    Args:
        data: 源字典
        key: 键名
        default: 默认值

    Returns:
        对应的值或默认值
    """
    return data.get(key, default)
