"""
内容模板工具
提供内容结构验证和内容块提取功能
"""

import re
from typing import Any, Dict, List, Optional, Union


def validate_rule_structure(rule_data: Dict[str, Any]) -> bool:
    """验证规则结构是否符合要求

    Args:
        rule_data: 规则数据

    Returns:
        bool: 是否有效
    """
    # 必须包含基本字段
    required_fields = ["id", "name", "type", "description"]
    for field in required_fields:
        if field not in rule_data:
            return False

    # 验证类型字段
    valid_types = ["agent", "auto", "manual", "always"]
    if rule_data.get("type") not in valid_types:
        # 如果类型无效，设置为默认值
        rule_data["type"] = "manual"

    # 确保items字段存在
    if "items" not in rule_data:
        rule_data["items"] = []

    # 确保examples字段存在
    if "examples" not in rule_data:
        rule_data["examples"] = []

    # 确保globs字段存在
    if "globs" not in rule_data:
        rule_data["globs"] = []

    # 确保always_apply字段存在
    if "always_apply" not in rule_data:
        rule_data["always_apply"] = False

    return True


def validate_document_structure(doc_data: Dict[str, Any]) -> bool:
    """验证文档结构是否符合要求

    Args:
        doc_data: 文档数据

    Returns:
        bool: 是否有效
    """
    # 必须包含基本字段
    required_fields = ["id", "title", "description"]
    for field in required_fields:
        if field not in doc_data:
            return False

    # 确保blocks字段存在
    if "blocks" not in doc_data:
        doc_data["blocks"] = []

    return True


def extract_blocks_from_content(content: str) -> List[Dict[str, Any]]:
    """从内容中提取内容块

    Args:
        content: 文本内容

    Returns:
        List[Dict]: 内容块列表
    """
    blocks = []

    # 提取标题块
    heading_pattern = r"^(#{1,6})\s+(.+)$"
    for i, line in enumerate(content.split("\n")):
        match = re.match(heading_pattern, line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            blocks.append({"id": f"h{level}_{i}", "type": "heading", "level": level, "content": title})

    # 提取代码块
    code_pattern = r"```([a-zA-Z]*)\n([\s\S]*?)```"
    for i, match in enumerate(re.finditer(code_pattern, content)):
        language = match.group(1) or "text"
        code_content = match.group(2)
        blocks.append({"id": f"code_{i}", "type": "code", "language": language, "content": code_content})

    # 提取引用块
    quote_pattern = r"((?:^>\s+.+\n?)+)"
    for i, match in enumerate(re.finditer(quote_pattern, content, re.MULTILINE)):
        quote_content = match.group(1)
        blocks.append({"id": f"quote_{i}", "type": "quote", "content": quote_content})

    # 提取列表块
    list_pattern = r"(?:^[*-]\s+.+$(?:\n[*-]\s+.+$)+)"
    for i, match in enumerate(re.finditer(list_pattern, content, re.MULTILINE)):
        list_content = match.group(0)
        blocks.append({"id": f"list_{i}", "type": "list", "content": list_content})

    # 提取表格块
    table_pattern = r"(\|.+\|(?:\n\|.+\|)+)"
    for i, match in enumerate(re.finditer(table_pattern, content)):
        table_content = match.group(1)
        blocks.append({"id": f"table_{i}", "type": "table", "content": table_content})

    # 提取水平线
    hr_pattern = r"^(---|\*\*\*|___)\s*$"
    for i, line in enumerate(content.split("\n")):
        if re.match(hr_pattern, line):
            blocks.append({"id": f"hr_{i}", "type": "hr", "content": line})

    return blocks


def create_document_template() -> Dict[str, Any]:
    """创建文档模板

    Returns:
        Dict: 文档模板
    """
    return {"id": "new_document", "title": "新文档", "description": "文档描述", "blocks": []}


def create_generic_template() -> Dict[str, Any]:
    """创建通用内容模板

    Returns:
        Dict: 通用内容模板
    """
    return {
        "id": "new_content",
        "title": "新内容",
        "description": "",
        "type": "generic",
        "key_points": [],
        "summary": "",
    }
