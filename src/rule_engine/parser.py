#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则解析器

提供解析规则文件内容的功能
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


def parse_rule_content(content: str) -> Dict[str, Any]:
    """
    解析规则内容

    Args:
        content: 规则文件内容

    Returns:
        Dict[str, Any]: 解析后的规则数据，包含metadata和sections
    """
    try:
        # 分离Front Matter和Markdown内容
        meta, body = _split_front_matter(content)

        # 解析Front Matter（元数据）
        if meta:
            try:
                meta_data = yaml.safe_load(meta)
            except Exception as e:
                logger.error(f"解析Front Matter失败: {str(e)}")
                meta_data = {}
        else:
            meta_data = {}

        # 解析Markdown内容
        sections = _parse_markdown_sections(body)

        # 组合结果
        result = {"metadata": meta_data, "sections": sections}

        return result

    except Exception as e:
        logger.error(f"解析规则内容时出错: {str(e)}", exc_info=True)
        return {"metadata": {}, "sections": {}}


def _split_front_matter(content: str) -> Tuple[str, str]:
    """分离Front Matter和Markdown内容"""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if match:
        return match.group(1), match.group(2)
    else:
        return "", content


def _parse_markdown_sections(content: str) -> Dict[str, Any]:
    """解析Markdown内容中的不同部分"""
    sections = {}

    # 查找所有二级标题
    h2_pattern = r"^##\s+(.*?)$"
    h2_matches = re.finditer(h2_pattern, content, re.MULTILINE)

    # 提取每个部分的内容
    positions = []
    for match in h2_matches:
        positions.append((match.start(), match.group(1)))

    if not positions:
        return {}

    # 处理每个部分
    for i, (pos, title) in enumerate(positions):
        # 确定内容的结束位置
        if i < len(positions) - 1:
            end_pos = positions[i + 1][0]
        else:
            end_pos = len(content)

        # 提取内容
        section_content = content[pos:end_pos].strip()
        section_content = re.sub(r"^##\s+.*?$", "", section_content, 1, re.MULTILINE).strip()

        # 规范化标题为键名
        key = _normalize_key(title)

        # 处理特殊部分
        if key == "process" or key == "flow" or key == "steps" or key == "rules" or key == "examples":
            sections[key] = section_content  # 保存原始内容，不进行解析
        else:
            sections[key] = section_content

    return sections


def _normalize_key(title: str) -> str:
    """将标题规范化为键名"""
    # 转换为小写
    key = title.lower()

    # 移除特殊字符并用下划线替换空格
    key = re.sub(r"[^\w\s]", "", key)
    key = re.sub(r"\s+", "_", key)

    return key


def _parse_list_items(content: str) -> List[Dict[str, Any]]:
    """
    解析列表项

    Args:
        content: 列表内容字符串

    Returns:
        List[Dict[str, Any]]: 解析后的列表项
    """
    # 移除内容开头的空行
    content = content.lstrip()

    # 解析YAML格式的列表
    try:
        # 如果内容以破折号开头，尝试作为YAML列表解析
        if content.startswith("-"):
            return yaml.safe_load(content)
        else:
            # 否则尝试解析Markdown列表
            items = []
            current_item = {}

            # 识别列表项标记，如 "1. " 或 "- "
            list_item_pattern = r"^(?:\d+\.|\*|-)\s+(.*?)$"

            lines = content.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i]
                list_match = re.match(list_item_pattern, line)

                if list_match:
                    if current_item:  # 保存之前的项目
                        items.append(current_item)

                    # 开始新的项目
                    current_item = {"content": list_match.group(1).strip()}

                    # 收集多行内容，直到下一个列表项或内容结束
                    content_lines = []
                    j = i + 1
                    while j < len(lines) and not re.match(list_item_pattern, lines[j]):
                        content_lines.append(lines[j])
                        j += 1
                    i = j - 1  # 更新外部循环索引

                    if content_lines:
                        current_item["content"] += "\n" + "\n".join(content_lines)
                i += 1

            if current_item:  # 添加最后一个项目
                items.append(current_item)

            return items
    except Exception as e:
        logger.error(f"解析列表项时出错: {str(e)}")
        return []
