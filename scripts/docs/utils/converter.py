#!/usr/bin/env python
"""
标准Markdown和Obsidian格式之间的转换工具。

本模块提供两个主要的转换类：
- MDToObsidian：将标准Markdown转换为Obsidian Wiki风格
- ObsidianToMD：将Obsidian Wiki风格转换为标准Markdown

这个适配层利用了现有的开源库，避免重复造轮子。
"""

import logging
import os
import re
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

# 定义不进行同步的文件模式
DEFAULT_EXCLUDE_PATTERNS = {
    # Docusaurus特定文件
    r".*_category_\.json$",
    r".*\.docusaurus/.*",
    r".*\.DS_Store$",
    # Obsidian配置文件
    r".*\.obsidian/app\.json$",
    r".*\.obsidian/appearance\.json$",
    r".*\.obsidian/core-plugins\.json$",
    r".*\.obsidian/workspace\.json$",
    r".*\.obsidian/workspace\.json\.bak$",
    r".*\.obsidian/plugins/.*",
    # 排除website目录下的Docusaurus生成文件
    r".*/website/docs/.*",
}


class MDToObsidian:
    """
    将标准Markdown转换为Obsidian Wiki风格的转换器。

    主要处理以下转换：
    1. 标准链接 [文本](路径.md) -> [[路径|文本]]
    2. 处理相对路径和绝对路径
    3. 优化frontmatter以适应Obsidian
    """

    def __init__(
        self,
        preserve_front_matter: bool = True,
        preserve_images: bool = True,
        exclude_patterns: Optional[Set[str]] = None,
    ):
        """
        初始化转换器。

        Args:
            preserve_front_matter: 是否保留frontmatter
            preserve_images: 是否保留图片链接格式
            exclude_patterns: 要排除的文件模式集合
        """
        self.preserve_front_matter = preserve_front_matter
        self.preserve_images = preserve_images
        self.exclude_patterns = exclude_patterns or DEFAULT_EXCLUDE_PATTERNS
        self.logger = logging.getLogger(__name__)

    def should_exclude(self, file_path: str) -> bool:
        """
        判断文件是否应该被排除。

        Args:
            file_path: 文件路径

        Returns:
            bool: 如果文件应该被排除则返回True
        """
        normalized_path = os.path.normpath(file_path)
        return any(re.match(pattern, normalized_path) for pattern in self.exclude_patterns)

    def convert_file(
        self, source: str, target: str, logger: Optional[logging.Logger] = None
    ) -> bool:
        """
        将标准Markdown文件转换为Obsidian格式。

        Args:
            source: 源文件路径
            target: 目标文件路径
            logger: 可选的日志记录器

        Returns:
            bool: 转换是否成功
        """
        if logger:
            self.logger = logger

        # 检查文件是否应该被排除
        if self.should_exclude(source) or self.should_exclude(target):
            self.logger.info(f"跳过排除的文件: {source}")
            return True

        # 检查是否涉及website/docs目录
        if "website/docs" in source or "website/docs" in target:
            self.logger.info(f"跳过website/docs目录下的文件: {source}")
            return True

        try:
            self.logger.info(f"转换文件: {source} -> {target}")

            # 确保目标目录存在
            os.makedirs(os.path.dirname(target), exist_ok=True)

            # 读取源文件
            with open(source, "r", encoding="utf-8") as f:
                content = f.read()

            # 转换内容
            converted_content = self.convert_content(
                content, os.path.dirname(source), os.path.dirname(target)
            )

            # 写入目标文件
            with open(target, "w", encoding="utf-8") as f:
                f.write(converted_content)

            return True
        except Exception as e:
            self.logger.error(f"转换失败: {e}")
            return False

    def convert_content(self, content: str, source_dir: str, target_dir: str) -> str:
        """
        转换Markdown内容为Obsidian格式。

        Args:
            content: 原始Markdown内容
            source_dir: 源文件目录路径
            target_dir: 目标文件目录路径

        Returns:
            str: 转换后的内容
        """
        # 分离frontmatter和内容
        frontmatter, main_content = self._split_frontmatter(content)

        # 转换主要内容
        converted_content = main_content

        # 转换标准链接为Wiki链接，但排除图片链接
        if self.preserve_images:
            # 先处理非图片的标准链接
            converted_content = self._convert_normal_links(converted_content)
        else:
            # 所有链接都转换
            converted_content = self._convert_all_links(converted_content)

        # 重新组合frontmatter和内容
        if frontmatter and self.preserve_front_matter:
            return f"{frontmatter}\n\n{converted_content}"

        return converted_content

    def _split_frontmatter(self, content: str) -> Tuple[str, str]:
        """
        分离frontmatter和主要内容。

        Args:
            content: 原始内容

        Returns:
            Tuple[str, str]: (frontmatter, 主要内容)
        """
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.search(frontmatter_pattern, content, re.DOTALL)

        if match:
            frontmatter = f"---\n{match.group(1)}\n---"
            main_content = content[match.end() :]
            return frontmatter, main_content

        return "", content

    def _convert_normal_links(self, content: str) -> str:
        """
        转换非图片的标准链接为Wiki链接。

        Args:
            content: 原始内容

        Returns:
            str: 转换后的内容
        """

        # 排除图片链接(!开头)，转换标准链接
        def replace_links(match):
            if match.group(0).startswith("!"):
                return match.group(0)  # 保留图片链接格式

            text = match.group(1)
            link = match.group(2)

            # 移除.md扩展名
            if link.endswith(".md"):
                link = link[:-3]

            return f"[[{link}|{text}]]"

        # 匹配非图片的标准Markdown链接
        pattern = r"(?<!!)\[([^\]]+)\]\(([^)]+)(?:\.md)?\)"
        return re.sub(pattern, replace_links, content)

    def _convert_all_links(self, content: str) -> str:
        """
        转换所有标准链接为Wiki链接或嵌入。

        Args:
            content: 原始内容

        Returns:
            str: 转换后的内容
        """

        # 转换所有链接，包括图片链接
        def replace_links(match):
            is_image = match.group(0).startswith("!")
            text = match.group(1)
            link = match.group(2)

            # 移除.md扩展名
            if link.endswith(".md"):
                link = link[:-3]

            if is_image:
                return f"![[{link}]]"
            else:
                return f"[[{link}|{text}]]"

        # 匹配所有Markdown链接，包括图片链接
        pattern = r"(!?)\[([^\]]+)\]\(([^)]+)(?:\.md)?\)"
        return re.sub(pattern, replace_links, content)


class ObsidianToMD:
    """
    将Obsidian Wiki风格转换为标准Markdown的转换器。

    主要处理以下转换：
    1. Wiki链接 [[路径|文本]] -> [文本](路径.md)
    2. 简单Wiki链接 [[路径]] -> [路径](路径.md)
    3. 嵌入链接 ![[路径]] -> ![路径](路径.md)
    """

    def __init__(
        self, preserve_front_matter: bool = True, exclude_patterns: Optional[Set[str]] = None
    ):
        """
        初始化转换器。

        Args:
            preserve_front_matter: 是否保留frontmatter
            exclude_patterns: 要排除的文件模式集合
        """
        self.preserve_front_matter = preserve_front_matter
        self.exclude_patterns = exclude_patterns or DEFAULT_EXCLUDE_PATTERNS
        self.logger = logging.getLogger(__name__)

    def should_exclude(self, file_path: str) -> bool:
        """
        判断文件是否应该被排除。

        Args:
            file_path: 文件路径

        Returns:
            bool: 如果文件应该被排除则返回True
        """
        normalized_path = os.path.normpath(file_path)
        return any(re.match(pattern, normalized_path) for pattern in self.exclude_patterns)

    def convert_file(
        self, source: str, target: str, logger: Optional[logging.Logger] = None
    ) -> bool:
        """
        将Obsidian格式的文件转换为标准Markdown。

        Args:
            source: 源文件路径
            target: 目标文件路径
            logger: 可选的日志记录器

        Returns:
            bool: 转换是否成功
        """
        if logger:
            self.logger = logger

        # 检查文件是否应该被排除
        if self.should_exclude(source) or self.should_exclude(target):
            self.logger.info(f"跳过排除的文件: {source}")
            return True

        try:
            self.logger.info(f"转换文件: {source} -> {target}")

            # 确保目标目录存在
            os.makedirs(os.path.dirname(target), exist_ok=True)

            # 读取源文件
            with open(source, "r", encoding="utf-8") as f:
                content = f.read()

            # 转换内容
            converted_content = self.convert_content(
                content, os.path.dirname(source), os.path.dirname(target)
            )

            # 写入目标文件
            with open(target, "w", encoding="utf-8") as f:
                f.write(converted_content)

            return True
        except Exception as e:
            self.logger.error(f"转换失败: {e}")
            return False

    def convert_content(self, content: str, source_dir: str, target_dir: str) -> str:
        """
        转换Obsidian格式内容为标准Markdown。

        Args:
            content: 原始Obsidian内容
            source_dir: 源文件目录路径
            target_dir: 目标文件目录路径

        Returns:
            str: 转换后的内容
        """
        # 分离frontmatter和内容
        frontmatter, main_content = self._split_frontmatter(content)

        # 转换主要内容
        converted_content = main_content

        # 转换Wiki链接为标准链接
        converted_content = self._convert_wiki_links_with_text(converted_content)
        converted_content = self._convert_simple_wiki_links(converted_content)
        converted_content = self._convert_embedded_links(converted_content)

        # 重新组合frontmatter和内容
        if frontmatter and self.preserve_front_matter:
            return f"{frontmatter}\n\n{converted_content}"

        return converted_content

    def _split_frontmatter(self, content: str) -> Tuple[str, str]:
        """
        分离frontmatter和主要内容。

        Args:
            content: 原始内容

        Returns:
            Tuple[str, str]: (frontmatter, 主要内容)
        """
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.search(frontmatter_pattern, content, re.DOTALL)

        if match:
            frontmatter = f"---\n{match.group(1)}\n---"
            main_content = content[match.end() :]
            return frontmatter, main_content

        return "", content

    def _convert_wiki_links_with_text(self, content: str) -> str:
        """
        转换带显示文本的Wiki链接为标准链接。

        Args:
            content: 原始内容

        Returns:
            str: 转换后的内容
        """
        # 转换 [[路径|文本]] -> [文本](路径.md)
        pattern = r"\[\[([^|\]]+)\|([^\]]+)\]\]"
        return re.sub(pattern, r"[\2](\1.md)", content)

    def _convert_simple_wiki_links(self, content: str) -> str:
        """
        转换简单Wiki链接为标准链接。

        Args:
            content: 原始内容

        Returns:
            str: 转换后的内容
        """
        # 转换 [[路径]] -> [路径](路径.md)
        pattern = r"\[\[([^\]|]+)\]\]"
        return re.sub(pattern, r"[\1](\1.md)", content)

    def _convert_embedded_links(self, content: str) -> str:
        """
        转换嵌入链接为图片链接。

        Args:
            content: 原始内容

        Returns:
            str: 转换后的内容
        """
        # 转换 ![[路径]] -> ![路径](路径)
        # 注意：这里不添加.md扩展名，因为嵌入通常是图片或其他非Markdown文件
        pattern = r"!\[\[([^\]]+)\]\]"

        def replace_embed(match):
            path = match.group(1)
            # 如果是图片，确保不添加.md扩展名
            if any(path.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".svg"]):
                return f"![{path}]({path})"
            # 对于非图片文件，添加.md扩展名
            else:
                return f"![{path}]({path}.md)"

        return re.sub(pattern, replace_embed, content)


# 如果直接运行此脚本，提供简单的命令行界面
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="在标准Markdown和Obsidian格式之间转换")
    parser.add_argument("source", help="源文件或目录")
    parser.add_argument("target", help="目标文件或目录")
    parser.add_argument("--mode", choices=["to-obsidian", "to-md"], required=True, help="转换模式")
    parser.add_argument("--recursive", action="store_true", help="递归处理目录")
    parser.add_argument("--include-excluded", action="store_true", help="包含通常被排除的文件")

    args = parser.parse_args()

    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # 创建转换器
    exclude_patterns = set() if args.include_excluded else DEFAULT_EXCLUDE_PATTERNS

    if args.mode == "to-obsidian":
        converter = MDToObsidian(exclude_patterns=exclude_patterns)
    else:
        converter = ObsidianToMD(exclude_patterns=exclude_patterns)

    # 处理文件或目录
    source_path = Path(args.source)
    target_path = Path(args.target)

    if source_path.is_file():
        # 处理单个文件
        if target_path.is_dir():
            target_file = target_path / source_path.name
        else:
            target_file = target_path

        converter.convert_file(str(source_path), str(target_file), logger)

    elif source_path.is_dir() and args.recursive:
        # 递归处理目录
        for root, dirs, files in os.walk(str(source_path)):
            rel_path = os.path.relpath(root, str(source_path))
            target_dir = target_path / rel_path

            for file in files:
                if file.endswith(".md"):
                    source_file = Path(root) / file
                    target_file = target_dir / file

                    os.makedirs(target_dir, exist_ok=True)
                    converter.convert_file(str(source_file), str(target_file), logger)

    elif source_path.is_dir():
        # 仅处理目录下的文件（不递归）
        for file in source_path.glob("*.md"):
            target_file = target_path / file.name
            converter.convert_file(str(file), str(target_file), logger)

    else:
        logger.error(f"源路径不存在: {source_path}")
