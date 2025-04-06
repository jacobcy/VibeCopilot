"""
链接转换模块

处理Obsidian链接到Docusaurus链接的转换
"""

import shutil
from pathlib import Path
from typing import Union

from .base import BaseConverter, logger
from .file_mapping import FileMappingHandler


class LinkConverter(FileMappingHandler):
    """链接转换器"""

    def convert_links(self, content: str, file_path: Path) -> str:
        """
        转换Obsidian链接为Docusaurus链接

        Args:
            content: 文档内容
            file_path: 文件路径（相对于obsidian_dir）

        Returns:
            转换后的内容
        """
        # 确保文件映射已构建
        self.ensure_file_mapping()

        current_dir = file_path.parent

        # 转换嵌入内容
        def embed_replacer(match):
            target_file = match.group(1).strip()
            display_text = match.group(3) or ""

            # 如果有扩展名且是图片
            if self.is_image_file(target_file):
                # 复制资源文件
                source_path = self.assets_dir / target_file
                if source_path.exists():
                    # 目标路径
                    rel_assets_dir = Path("assets")
                    target_assets_dir = self.docusaurus_dir / rel_assets_dir
                    target_assets_dir.mkdir(parents=True, exist_ok=True)

                    # 复制文件
                    shutil.copy2(source_path, target_assets_dir / target_file)

                    # 构建相对路径
                    rel_path = f"/{rel_assets_dir}/{target_file}"

                    # 返回Markdown图片语法
                    if display_text:
                        return f"![{display_text}]({rel_path})"
                    else:
                        return f"![{target_file}]({rel_path})"
                else:
                    logger.warning(f"嵌入的图片未找到: {source_path}")
                    return f"![Image not found: {target_file}](/img/missing.png)"
            else:
                # 查找目标文件
                if target_file in self.file_mapping:
                    target_path = self.file_mapping[target_file]
                    rel_path = self.get_relative_path(
                        self.docusaurus_dir / target_path.with_suffix(""),
                        self.docusaurus_dir / file_path.parent,
                    )

                    # 保留Markdown语法但链接到目标
                    if display_text:
                        return f"import {{DisplayContent}} from '@site/src/components/DisplayContent';\n\n<DisplayContent path=\"{rel_path}\">{display_text}</DisplayContent>"
                    else:
                        return f"import {{DisplayContent}} from '@site/src/components/DisplayContent';\n\n<DisplayContent path=\"{rel_path}\" />"
                else:
                    logger.warning(f"嵌入的文档未找到: {target_file}")
                    return f"*Content not found: {target_file}*"

        # 转换普通链接
        def link_replacer(match):
            target_file = match.group(1).strip()
            section = match.group(2)
            display_text = match.group(3) or target_file

            # 查找目标文件
            if target_file in self.file_mapping:
                target_path = self.file_mapping[target_file]
                # 计算相对路径（去除.md扩展名以符合Docusaurus要求）
                rel_path = self.get_relative_path(target_path.with_suffix(""), file_path.parent)

                # 添加锚点（如果有）
                if section:
                    rel_path = f"{rel_path}#{section.lower().replace(' ', '-')}"

                return f"[{display_text}]({rel_path})"
            else:
                logger.warning(f"链接的文档未找到: {target_file}")
                return f"[{display_text} (链接不存在)](#{target_file.lower().replace(' ', '-')})"

        # 先处理嵌入，再处理普通链接
        content = self.obsidian_embed_regex.sub(embed_replacer, content)
        content = self.obsidian_link_regex.sub(link_replacer, content)

        return content
