"""
ChromaDB向量存储工具函数

提供ChromaDB向量存储实现所需的工具函数和常量。
"""

import logging
import os
from typing import Any, Dict, Optional

# 默认数据目录
DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), "Public", "VibeCopilot", "data", "chroma_db")

logger = logging.getLogger(__name__)


def generate_permalink(folder: str, doc_id: str) -> str:
    """生成永久链接"""
    return f"memory://{folder}/{doc_id}"


def parse_permalink(permalink: str) -> Optional[Dict[str, str]]:
    """
    解析永久链接

    Args:
        permalink: 永久链接

    Returns:
        包含folder和doc_id的字典，解析失败返回None
    """
    if not permalink.startswith("memory://"):
        return None

    parts = permalink[len("memory://") :].split("/", 1)
    if len(parts) != 2:
        return None

    folder, doc_id = parts
    return {"folder": folder, "doc_id": doc_id}


def create_chroma_filter(filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    创建ChromaDB格式的过滤器

    Args:
        filter_dict: 过滤条件

    Returns:
        ChromaDB格式的过滤器
    """
    if not filter_dict:
        return None

    # 移除folder键，因为它用于选择集合
    filter_copy = {k: v for k, v in filter_dict.items() if k != "folder"}

    if not filter_copy:
        return None

    # 构建ChromaDB格式的过滤器
    return {"$and": [{"$eq": {k: v}} for k, v in filter_copy.items()]}
