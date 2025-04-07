#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则解析器

解析 .mdc 规则文件，提取结构化信息
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


class RuleParser:
    """规则解析器，负责从.mdc文件中解析规则结构"""

    def __init__(self):
        self.front_matter_pattern = re.compile(r"^---\s*$(.+?)^---\s*$", re.MULTILINE | re.DOTALL)
        self.section_pattern = re.compile(r"^#+\s*(.+?)\s*$", re.MULTILINE)
        self.subsection_pattern = re.compile(r"^#{2,}\s*(.+?)\s*$", re.MULTILINE)

    def parse_rule_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        解析规则文件

        Args:
            file_path: 规则文件路径

        Returns:
            解析后的规则数据
        """
        if not os.path.exists(file_path):
            logger.error(f"规则文件不存在: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 解析规则元数据和内容
            rule_data = self._parse_rule_content(content)

            # 添加规则来源
            rule_data["source_file"] = file_path
            rule_data["rule_id"] = os.path.splitext(os.path.basename(file_path))[0]

            return rule_data
        except Exception as e:
            logger.error(f"解析规则文件失败: {file_path}, 错误: {str(e)}")
            return None

    def _parse_rule_content(self, content: str) -> Dict[str, Any]:
        """
        解析规则内容

        Args:
            content: 规则文件内容

        Returns:
            解析后的规则数据
        """
        result = {"metadata": {}, "sections": [], "raw_content": content}

        # 解析front matter
        front_matter_match = self.front_matter_pattern.search(content)
        if front_matter_match:
            try:
                front_matter = front_matter_match.group(1)
                result["metadata"] = yaml.safe_load(front_matter)

                # 移除front matter部分
                content = content[front_matter_match.end() :].strip()
            except Exception as e:
                logger.warning(f"解析front matter失败: {str(e)}")

        # 查找所有一级标题，作为主要段落分隔点
        section_positions = [
            (m.start(), m.group(1)) for m in self.section_pattern.finditer(content)
        ]

        if not section_positions:
            # 如果没有找到标题，将整个内容作为一个部分
            result["sections"].append(
                {"title": "内容", "content": content.strip(), "subsections": []}
            )
            return result

        # 解析每个部分的内容
        for i, (pos, title) in enumerate(section_positions):
            next_pos = (
                len(content) if i == len(section_positions) - 1 else section_positions[i + 1][0]
            )
            section_content = content[pos:next_pos].strip()

            # 跳过标题行
            section_content = self.section_pattern.sub("", section_content, 1).strip()

            # 查找子部分
            subsections = self._parse_subsections(section_content)

            result["sections"].append(
                {"title": title, "content": section_content, "subsections": subsections}
            )

        return result

    def _parse_subsections(self, content: str) -> List[Dict[str, str]]:
        """
        解析子部分

        Args:
            content: 部分内容

        Returns:
            子部分列表
        """
        subsection_positions = [
            (m.start(), m.group(1)) for m in self.subsection_pattern.finditer(content)
        ]

        if not subsection_positions:
            return []

        subsections = []

        for i, (pos, title) in enumerate(subsection_positions):
            next_pos = (
                len(content)
                if i == len(subsection_positions) - 1
                else subsection_positions[i + 1][0]
            )
            subsection_content = content[pos:next_pos].strip()

            # 跳过标题行
            subsection_content = self.subsection_pattern.sub("", subsection_content, 1).strip()

            subsections.append({"title": title, "content": subsection_content})

        return subsections
