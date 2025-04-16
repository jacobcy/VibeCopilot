"""
记忆管理器工具函数

提供记忆管理器使用的工具函数和辅助方法
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def extract_original_content(content: str) -> str:
    """
    从增强文本中提取原始内容

    Args:
        content: 可能包含增强文本的内容

    Returns:
        提取的原始内容
    """
    if "原文:" in content:
        return content.split("原文:", 1)[1].strip()
    return content


def create_enhanced_text(title: str, entities: list, relations: list, content: str) -> str:
    """
    创建增强文本

    Args:
        title: 记忆标题
        entities: 实体列表
        relations: 关系列表
        content: 原始内容

    Returns:
        增强后的文本
    """
    enhanced_text = f"标题: {title}\n\n"

    if entities:
        entity_names = [e.get("name", "") for e in entities if e.get("name")]
        enhanced_text += f"实体: {', '.join(entity_names)}\n\n"

    if relations:
        relation_descs = [r.get("description", "") for r in relations if r.get("description")]
        enhanced_text += f"关系: {', '.join(relation_descs)}\n\n"

    enhanced_text += f"原文: {content}"

    return enhanced_text


def create_memory_metadata(
    title: str, tags: str, entities: list, relations: list, observations: list, folder: str, memory_item_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    创建记忆元数据

    Args:
        title: 记忆标题
        tags: 标签
        entities: 实体列表
        relations: 关系列表
        observations: 观察列表
        folder: 文件夹
        memory_item_id: 关联的记忆项ID

    Returns:
        元数据字典
    """
    metadata = {
        "title": title,
        "tags": tags,
        "entity_count": len(entities),
        "relation_count": len(relations),
        "observation_count": len(observations),
        "content_type": "memory",
        "folder": folder,
    }

    if memory_item_id:
        metadata["memory_item_id"] = memory_item_id

    return metadata


def format_error_response(message: str, permalink: Optional[str] = None) -> Dict[str, Any]:
    """
    创建错误响应

    Args:
        message: 错误信息
        permalink: 可选的记忆永久链接

    Returns:
        错误响应字典
    """
    response = {"success": False, "message": message}

    if permalink:
        response["permalink"] = permalink

    return response


def format_success_response(message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    创建成功响应

    Args:
        message: 成功信息
        data: 响应数据

    Returns:
        成功响应字典
    """
    response = {"success": True, "message": message}

    if data:
        response.update(data)

    return response
