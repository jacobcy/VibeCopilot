"""
ID生成器模块

提供文档、块和链接的唯一ID生成函数
"""

import uuid


def generate_document_id() -> str:
    """生成文档ID

    Returns:
        唯一文档ID，格式为"doc-{uuid4}"
    """
    return f"doc-{uuid.uuid4()}"


def generate_block_id() -> str:
    """生成块ID

    Returns:
        唯一块ID，格式为"blk-{uuid4}"
    """
    return f"blk-{uuid.uuid4()}"


def generate_link_id() -> str:
    """生成链接ID

    Returns:
        唯一链接ID，格式为"lnk-{uuid4}"
    """
    return f"lnk-{uuid.uuid4()}"


def is_valid_document_id(doc_id: str) -> bool:
    """验证文档ID格式是否有效

    Args:
        doc_id: 文档ID

    Returns:
        是否有效
    """
    if not doc_id.startswith("doc-"):
        return False

    # 尝试解析UUID部分
    try:
        uuid_part = doc_id[4:]  # 跳过"doc-"前缀
        uuid.UUID(uuid_part)
        return True
    except ValueError:
        return False


def is_valid_block_id(block_id: str) -> bool:
    """验证块ID格式是否有效

    Args:
        block_id: 块ID

    Returns:
        是否有效
    """
    if not block_id.startswith("blk-"):
        return False

    # 尝试解析UUID部分
    try:
        uuid_part = block_id[4:]  # 跳过"blk-"前缀
        uuid.UUID(uuid_part)
        return True
    except ValueError:
        return False


def is_valid_link_id(link_id: str) -> bool:
    """验证链接ID格式是否有效

    Args:
        link_id: 链接ID

    Returns:
        是否有效
    """
    if not link_id.startswith("lnk-"):
        return False

    # 尝试解析UUID部分
    try:
        uuid_part = link_id[4:]  # 跳过"lnk-"前缀
        uuid.UUID(uuid_part)
        return True
    except ValueError:
        return False
