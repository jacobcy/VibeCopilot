"""
链接转换器 - 处理Obsidian与Docusaurus之间的链接格式转换.

提供双向链接转换、路径解析和引用完整性检查等功能.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class LinkConverter:
    """链接格式转换器，处理Obsidian与Docusaurus文档链接转换."""

    # Obsidian链接模式: [[文件名]] 或 [[文件名|显示文本]]
    OBSIDIAN_LINK_PATTERN = r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"

    # Obsidian嵌入模式: ![[文件名]]
    OBSIDIAN_EMBED_PATTERN = r"!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"

    def __init__(self, base_dir: str):
        """
        初始化链接转换器.

        Args:
            base_dir: 文档根目录的绝对路径
        """
        self.base_dir = Path(base_dir)
        self.obsidian_link_regex = re.compile(self.OBSIDIAN_LINK_PATTERN)
        self.obsidian_embed_regex = re.compile(self.OBSIDIAN_EMBED_PATTERN)

    def obsidian_to_docusaurus(self, content: str, file_path: str) -> str:
        """
        将Obsidian格式链接转换为Docusaurus兼容格式.

        Args:
            content: 文档内容
            file_path: 当前文件的相对路径(相对于base_dir)

        Returns:
            转换后的内容
        """
        # 获取当前文件的目录路径
        current_dir = Path(file_path).parent

        # 转换普通链接
        def link_replacer(match):
            target_file = match.group(1).strip()
            display_text = match.group(2) or target_file

            # 解析目标文件路径
            target_path = self._resolve_link_path(target_file, current_dir)
            if target_path:
                # 构建相对路径
                rel_path = os.path.relpath(target_path, current_dir)
                # 确保使用正斜杠
                rel_path = rel_path.replace("\\", "/")
                return f"[{display_text}]({rel_path})"

            # 如果无法解析路径，保留原始链接并添加警告
            return f"[{display_text}](#broken-link-{target_file})"

        # 转换嵌入内容
        def embed_replacer(match):
            target_file = match.group(1).strip()
            display_text = match.group(2) or ""

            # 解析目标文件路径
            target_path = self._resolve_link_path(target_file, current_dir)
            if target_path:
                # 构建相对路径
                rel_path = os.path.relpath(target_path, current_dir)
                # 确保使用正斜杠
                rel_path = rel_path.replace("\\", "/")

                # 根据文件类型进行不同处理
                extension = Path(target_file).suffix.lower()
                if extension in [".png", ".jpg", ".jpeg", ".gif", ".svg"]:
                    if display_text:
                        return f"![{display_text}]({rel_path})"
                    return f"![{Path(target_file).stem}]({rel_path})"
                else:
                    # 对于非图片文件，转换为导入语法
                    return f"import {{{Path(target_file).stem}}} from '{rel_path}';\n\n<{Path(target_file).stem} />"

            # 如果无法解析路径，保留原始链接并添加警告
            return f"<!-- 嵌入失败: {target_file} -->"

        # 先处理嵌入，再处理普通链接
        content = self.obsidian_embed_regex.sub(embed_replacer, content)
        content = self.obsidian_link_regex.sub(link_replacer, content)

        return content

    def docusaurus_to_obsidian(self, content: str) -> str:
        """
        将Docusaurus格式链接转换为Obsidian兼容格式.

        Args:
            content: 文档内容

        Returns:
            转换后的内容
        """
        # 匹配Markdown链接: [显示文本](链接地址)
        md_link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

        def md_link_replacer(match):
            display_text = match.group(1).strip()
            link_path = match.group(2).strip()

            # 如果是锚点链接或外部链接，保留原样
            if link_path.startswith("#") or link_path.startswith("http"):
                return match.group(0)

            # 去除扩展名并转换为Obsidian格式
            path_without_ext = Path(link_path).stem
            if display_text == path_without_ext:
                return f"[[{path_without_ext}]]"
            else:
                return f"[[{path_without_ext}|{display_text}]]"

        # 匹配图片链接: ![替代文本](图片路径)
        img_link_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"

        def img_link_replacer(match):
            alt_text = match.group(1).strip()
            img_path = match.group(2).strip()

            # 如果是外部图片链接，保留原样
            if img_path.startswith("http"):
                return match.group(0)

            # 转换为Obsidian嵌入格式
            if alt_text:
                return f"![[{img_path}|{alt_text}]]"
            else:
                return f"![[{img_path}]]"

        # 先处理图片链接，再处理普通链接
        content = re.sub(img_link_pattern, img_link_replacer, content)
        content = re.sub(md_link_pattern, md_link_replacer, content)

        return content

    def _resolve_link_path(self, link_target: str, current_dir: Path) -> Optional[Path]:
        """
        解析Obsidian链接目标的实际路径.

        Args:
            link_target: Obsidian链接目标
            current_dir: 当前文件所在目录

        Returns:
            解析后的目标路径，如果无法解析则返回None
        """
        # 如果有扩展名，直接在当前目录查找
        if "." in link_target:
            # 尝试相对于当前目录解析
            target_path = current_dir / link_target
            if target_path.exists():
                return target_path

        # 如果没有扩展名，尝试添加.md扩展名
        target_with_md = f"{link_target}.md"
        target_path = current_dir / target_with_md

        if target_path.exists():
            return target_path

        # 如果在当前目录找不到，尝试在整个文档库中查找
        for ext in [".md", ".mdx", ".markdown"]:
            for file_path in self.base_dir.glob(f"**/*{ext}"):
                if file_path.stem == link_target:
                    return file_path

        # 查找带空格的文件名
        for ext in [".md", ".mdx", ".markdown"]:
            for file_path in self.base_dir.glob(f"**/*{ext}"):
                if file_path.stem.replace(" ", "_") == link_target:
                    return file_path

        return None

    def validate_links(self, content: str, file_path: str) -> List[Dict]:
        """
        验证文档中的链接是否有效.

        Args:
            content: 文档内容
            file_path: 当前文件路径

        Returns:
            无效链接列表，每项包含链接文本和位置信息
        """
        current_dir = Path(file_path).parent
        broken_links = []

        # 检查Obsidian链接
        for match in self.obsidian_link_regex.finditer(content):
            target_file = match.group(1).strip()
            if not self._resolve_link_path(target_file, current_dir):
                broken_links.append(
                    {
                        "type": "obsidian_link",
                        "target": target_file,
                        "position": match.span(),
                        "text": match.group(0),
                    }
                )

        # 检查Obsidian嵌入
        for match in self.obsidian_embed_regex.finditer(content):
            target_file = match.group(1).strip()
            if not self._resolve_link_path(target_file, current_dir):
                broken_links.append(
                    {
                        "type": "obsidian_embed",
                        "target": target_file,
                        "position": match.span(),
                        "text": match.group(0),
                    }
                )

        return broken_links
