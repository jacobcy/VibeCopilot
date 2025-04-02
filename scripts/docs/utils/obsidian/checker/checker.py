#!/usr/bin/env python
"""
Obsidian语法检查工具的核心检查器
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from scripts.docs.utils.obsidian.checker.utils import (
    create_line_map,
    get_line_col,
    resolve_link_path,
)


class ObsidianSyntaxChecker:
    """Obsidian语法检查器，检查文档中的语法问题"""

    # Obsidian链接模式: [[文件名]] 或 [[文件名|显示文本]]
    OBSIDIAN_LINK_PATTERN = r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"

    # Obsidian嵌入模式: ![[文件名]]
    OBSIDIAN_EMBED_PATTERN = r"!\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"

    # MDX组件未闭合模式
    MDX_UNCLOSED_TABS_PATTERN = r"<Tabs>(?:(?!<\/Tabs>).)*$"

    # 数字开头的JSX标签
    MDX_NUMBER_TAG_PATTERN = r"<(\d+)([:\s])"

    # 不正确的结束标签
    MDX_WRONG_CLOSING_TAG_PATTERN = r"<\/([\w-]+):([\w-]+)>"

    # YAML前置元数据检测
    YAML_FRONTMATTER_PATTERN = r"^---\s*\n(.*?)\n---\s*$"

    def __init__(self, base_dir: str, logger: Optional[logging.Logger] = None):
        """初始化语法检查器

        Args:
            base_dir: 基础目录路径
            logger: 日志记录器
        """
        self.base_dir = Path(base_dir)
        self.logger = logger or logging.getLogger("obsidian_syntax_checker")

        # 编译正则表达式
        self.obsidian_link_regex = re.compile(self.OBSIDIAN_LINK_PATTERN)
        self.obsidian_embed_regex = re.compile(self.OBSIDIAN_EMBED_PATTERN)
        self.mdx_unclosed_tabs_regex = re.compile(self.MDX_UNCLOSED_TABS_PATTERN, re.DOTALL)
        self.mdx_number_tag_regex = re.compile(self.MDX_NUMBER_TAG_PATTERN)
        self.mdx_wrong_closing_tag_regex = re.compile(self.MDX_WRONG_CLOSING_TAG_PATTERN)
        self.yaml_frontmatter_regex = re.compile(self.YAML_FRONTMATTER_PATTERN, re.DOTALL)

    def check_file(self, file_path: Union[str, Path]) -> Dict[str, List[Dict]]:
        """检查单个文件的语法问题

        Args:
            file_path: 文件路径

        Returns:
            语法问题列表，按类型分组
        """
        file_path = Path(file_path)
        issues = {"errors": [], "warnings": [], "info": []}  # 需要修复的严重问题  # 建议修复的问题  # 信息性提示

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查各种语法问题
            self._check_links(content, file_path, issues)
            self._check_embeds(content, file_path, issues)
            self._check_mdx_syntax(content, file_path, issues)
            self._check_frontmatter(content, file_path, issues)

        except Exception as e:
            issues["errors"].append(
                {
                    "type": "file_error",
                    "message": f"无法读取或处理文件: {str(e)}",
                    "line": 0,
                    "column": 0,
                    "text": "",
                }
            )

        return issues

    def check_directory(
        self, directory: Union[str, Path], recursive: bool = True
    ) -> Dict[str, Dict]:
        """检查目录中的所有Markdown文件

        Args:
            directory: 目录路径
            recursive: 是否递归检查子目录

        Returns:
            所有文件的问题列表
        """
        directory = Path(directory)
        all_issues = {}

        # 查找所有Markdown文件
        pattern = "**/*.md" if recursive else "*.md"
        for md_file in directory.glob(pattern):
            file_issues = self.check_file(md_file)

            # 只添加有问题的文件
            if any(file_issues.values()):
                all_issues[str(md_file.relative_to(self.base_dir))] = file_issues

        return all_issues

    def _check_links(self, content: str, file_path: Path, issues: Dict[str, List[Dict]]):
        """检查Obsidian链接语法和引用完整性

        Args:
            content: 文档内容
            file_path: 文件路径
            issues: 问题收集字典
        """
        current_dir = file_path.parent

        # 获取行号映射
        line_map = create_line_map(content)

        # 检查每个Obsidian链接
        for match in self.obsidian_link_regex.finditer(content):
            target_file = match.group(1).strip()
            section = match.group(2)

            # 检查目标文件是否存在
            target_path = resolve_link_path(target_file, current_dir)
            if not target_path:
                # 查找行号和列号
                start_pos = match.start()
                line_no, col_no = get_line_col(start_pos, line_map)

                issues["warnings"].append(
                    {
                        "type": "broken_link",
                        "message": f"链接目标不存在: {target_file}",
                        "line": line_no,
                        "column": col_no,
                        "text": match.group(0),
                    }
                )

            # 如果链接包含段落引用，但目标文件存在
            elif section and target_path:
                # 这里可以添加进一步检查段落引用的完整性
                # 但需要读取目标文件内容，可能会影响性能
                pass

    def _check_embeds(self, content: str, file_path: Path, issues: Dict[str, List[Dict]]):
        """检查Obsidian嵌入语法和引用完整性

        Args:
            content: 文档内容
            file_path: 文件路径
            issues: 问题收集字典
        """
        current_dir = file_path.parent

        # 获取行号映射
        line_map = create_line_map(content)

        # 检查每个Obsidian嵌入
        for match in self.obsidian_embed_regex.finditer(content):
            target_file = match.group(1).strip()

            # 检查目标文件是否存在
            target_path = resolve_link_path(target_file, current_dir)
            if not target_path:
                # 查找行号和列号
                start_pos = match.start()
                line_no, col_no = get_line_col(start_pos, line_map)

                issues["warnings"].append(
                    {
                        "type": "broken_embed",
                        "message": f"嵌入目标不存在: {target_file}",
                        "line": line_no,
                        "column": col_no,
                        "text": match.group(0),
                    }
                )

    def _check_mdx_syntax(self, content: str, file_path: Path, issues: Dict[str, List[Dict]]):
        """检查MDX/JSX语法问题

        Args:
            content: 文档内容
            file_path: 文件路径
            issues: 问题收集字典
        """
        # 获取行号映射
        line_map = create_line_map(content)

        # 检查未闭合的Tabs组件
        for match in self.mdx_unclosed_tabs_regex.finditer(content):
            start_pos = match.start()
            line_no, col_no = get_line_col(start_pos, line_map)

            issues["errors"].append(
                {
                    "type": "unclosed_tabs",
                    "message": "未闭合的<Tabs>组件",
                    "line": line_no,
                    "column": col_no,
                    "text": match.group(0)[:50] + "..."
                    if len(match.group(0)) > 50
                    else match.group(0),
                }
            )

        # 检查数字开头的JSX标签
        for match in self.mdx_number_tag_regex.finditer(content):
            start_pos = match.start()
            line_no, col_no = get_line_col(start_pos, line_map)

            issues["errors"].append(
                {
                    "type": "numeric_tag",
                    "message": f"JSX标签不能以数字开头: <{match.group(1)}",
                    "line": line_no,
                    "column": col_no,
                    "text": match.group(0),
                }
            )

        # 检查错误的结束标签
        for match in self.mdx_wrong_closing_tag_regex.finditer(content):
            start_pos = match.start()
            line_no, col_no = get_line_col(start_pos, line_map)

            component = match.group(1)
            prop = match.group(2)
            issues["errors"].append(
                {
                    "type": "wrong_closing_tag",
                    "message": f"错误的结束标签: </{component}:{prop}>, 应为 </{component}>",
                    "line": line_no,
                    "column": col_no,
                    "text": match.group(0),
                }
            )

    def _check_frontmatter(self, content: str, file_path: Path, issues: Dict[str, List[Dict]]):
        """检查YAML前置元数据

        Args:
            content: 文档内容
            file_path: 文件路径
            issues: 问题收集字典
        """
        # 获取行号映射
        line_map = create_line_map(content)

        # 检查是否有YAML前置元数据
        frontmatter_match = self.yaml_frontmatter_regex.search(content)
        if not frontmatter_match:
            issues["info"].append(
                {
                    "type": "missing_frontmatter",
                    "message": "文档缺少YAML前置元数据",
                    "line": 1,
                    "column": 1,
                    "text": content[:50] + "..." if len(content) > 50 else content,
                }
            )
            return

        # 检查前置元数据内部是否有常见错误
        frontmatter_content = frontmatter_match.group(1)

        # 检查缩进不一致
        indent_pattern = r"^(\s+).*$"
        indents = set()
        for line in frontmatter_content.split("\n"):
            if not line.strip():
                continue

            indent_match = re.match(indent_pattern, line)
            if indent_match:
                indents.add(len(indent_match.group(1)))

        if len(indents) > 1:
            line_no, col_no = get_line_col(frontmatter_match.start(), line_map)
            issues["warnings"].append(
                {
                    "type": "inconsistent_indent",
                    "message": "YAML前置元数据缩进不一致",
                    "line": line_no,
                    "column": col_no,
                    "text": frontmatter_content[:50] + "..."
                    if len(frontmatter_content) > 50
                    else frontmatter_content,
                }
            )
