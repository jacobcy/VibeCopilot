"""
规则模板工具
提供规则结构验证和内容块提取功能
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


def extract_blocks_from_content(content: str) -> List[Dict[str, Any]]:
    """从内容中提取规则块

    Args:
        content: 规则内容

    Returns:
        List[Dict]: 规则块列表
    """
    blocks = []

    # 提取标题块
    heading_pattern = r"^(#{1,6})\s+(.+)$"
    for i, line in enumerate(content.split("\n")):
        match = re.match(heading_pattern, line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            if level <= 3:  # 只提取前三级标题
                blocks.append(
                    {"id": f"h{level}_{i}", "type": "heading", "level": level, "content": title}
                )

    # 提取代码块
    code_pattern = r"```([a-zA-Z]*)\n([\s\S]*?)```"
    for i, match in enumerate(re.finditer(code_pattern, content)):
        language = match.group(1) or "text"
        code_content = match.group(2)
        blocks.append(
            {"id": f"code_{i}", "type": "code", "language": language, "content": code_content}
        )

    # 提取示例块
    example_pattern = r"<example(?:\s+type=\"([^\"]+)\")?>[\s\n]*([\s\S]*?)[\s\n]*<\/example>"
    for i, match in enumerate(re.finditer(example_pattern, content)):
        example_type = match.group(1) or "valid"
        example_content = match.group(2).strip()
        blocks.append(
            {
                "id": f"example_{i}",
                "type": "example",
                "is_valid": example_type.lower() != "invalid",
                "content": example_content,
            }
        )

    # 提取列表块
    list_pattern = r"(?:^[*-]\s+.+$(?:\n[*-]\s+.+$)+)"
    for i, match in enumerate(re.finditer(list_pattern, content, re.MULTILINE)):
        list_content = match.group(0)
        blocks.append({"id": f"list_{i}", "type": "list", "content": list_content})

    # 提取段落块（如果未被其他块捕获）
    # 这个部分可能需要更复杂的逻辑来避免与其他块重叠

    return blocks


def create_rule_template(rule_type: str = "manual") -> Dict[str, Any]:
    """创建规则模板

    Args:
        rule_type: 规则类型

    Returns:
        Dict: 规则模板
    """
    return {
        "id": "new_rule",
        "name": "新规则",
        "type": rule_type,
        "description": "规则描述",
        "globs": [],
        "always_apply": False,
        "items": [],
        "examples": [],
    }
