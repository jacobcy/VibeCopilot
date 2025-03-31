#!/usr/bin/env python
"""
Obsidian到Docusaurus转换工具

这个脚本基于Obsidiosaurus项目，提供了将Obsidian格式的Markdown文件转换为
Docusaurus格式的功能。它处理链接转换、图片处理等任务。
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("obsidian_to_docusaurus")


class ObsidianDocusaurusConverter:
    """Obsidian到Docusaurus的转换器"""

    # Obsidian链接模式: [[文件名]] 或 [[文件名|显示文本]]
    OBSIDIAN_LINK_PATTERN = r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"

    # Obsidian嵌入模式: ![[文件名]]
    OBSIDIAN_EMBED_PATTERN = r"!\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"

    def __init__(
        self,
        obsidian_dir: Union[str, Path],
        docusaurus_dir: Union[str, Path],
        assets_dir: Optional[str] = None,
    ):
        """
        初始化转换器

        Args:
            obsidian_dir: Obsidian文档目录
            docusaurus_dir: Docusaurus文档目录
            assets_dir: 资源文件目录
        """
        self.obsidian_dir = Path(obsidian_dir)
        self.docusaurus_dir = Path(docusaurus_dir)
        self.assets_dir = Path(assets_dir) if assets_dir else self.obsidian_dir / "assets"

        # 确保目录存在
        self.docusaurus_dir.mkdir(parents=True, exist_ok=True)
        (self.docusaurus_dir / "assets").mkdir(parents=True, exist_ok=True)

        # 编译正则表达式
        self.obsidian_link_regex = re.compile(self.OBSIDIAN_LINK_PATTERN)
        self.obsidian_embed_regex = re.compile(self.OBSIDIAN_EMBED_PATTERN)

        # 存储文件映射
        self.file_mapping = {}

    def build_file_mapping(self) -> Dict[str, Path]:
        """
        构建Obsidian文件路径与文件的映射

        Returns:
            文件名到文件路径的映射
        """
        file_mapping = {}

        # 遍历所有Markdown文件
        for md_file in self.obsidian_dir.glob("**/*.md"):
            # 跳过.obsidian目录和资源目录
            if ".obsidian" in md_file.parts or "assets" in md_file.parts:
                continue

            # 使用文件名作为键（去除扩展名）
            file_mapping[md_file.stem] = md_file.relative_to(self.obsidian_dir)

        self.file_mapping = file_mapping
        logger.info(f"构建了 {len(file_mapping)} 个文件的映射")
        return file_mapping

    def convert_links(self, content: str, file_path: Path) -> str:
        """
        转换Obsidian链接为Docusaurus链接

        Args:
            content: 文档内容
            file_path: 文件路径（相对于obsidian_dir）

        Returns:
            转换后的内容
        """
        current_dir = file_path.parent

        # 转换嵌入内容
        def embed_replacer(match):
            target_file = match.group(1).strip()
            display_text = match.group(3) or ""

            # 如果有扩展名且是图片
            if "." in target_file and target_file.split(".")[-1].lower() in [
                "png",
                "jpg",
                "jpeg",
                "gif",
                "svg",
            ]:
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
                    rel_path = os.path.relpath(
                        str(self.docusaurus_dir / target_path).replace(".md", ""),
                        str(self.docusaurus_dir / file_path.parent),
                    )
                    # 处理Windows路径
                    rel_path = rel_path.replace("\\", "/")
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
                rel_path = os.path.relpath(
                    str(target_path).replace(".md", ""), str(file_path.parent)
                )
                # 处理Windows路径
                rel_path = rel_path.replace("\\", "/")

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

    def convert_file(self, file_path: Path) -> bool:
        """
        转换单个文件

        Args:
            file_path: 文件路径（相对于obsidian_dir）

        Returns:
            是否成功
        """
        source_path = self.obsidian_dir / file_path
        target_path = self.docusaurus_dir / file_path

        # 确保目标目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 读取源文件
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 转换链接
            converted_content = self.convert_links(content, file_path)

            # 写入目标文件
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(converted_content)

            logger.info(f"转换成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"转换失败: {file_path} - {str(e)}")
            return False

    def convert_all_files(self) -> Tuple[int, int]:
        """
        转换所有文件

        Returns:
            (成功数, 失败数)
        """
        # 构建文件映射
        self.build_file_mapping()

        success_count = 0
        failure_count = 0

        # 遍历所有Markdown文件
        for md_file in self.obsidian_dir.glob("**/*.md"):
            # 跳过.obsidian目录和资源目录
            if ".obsidian" in md_file.parts or "assets" in md_file.parts:
                continue

            # 计算相对路径
            rel_path = md_file.relative_to(self.obsidian_dir)

            # 转换文件
            if self.convert_file(rel_path):
                success_count += 1
            else:
                failure_count += 1

        # 复制资源目录
        if self.assets_dir.exists():
            for asset_file in self.assets_dir.glob("**/*"):
                if asset_file.is_file():
                    # 计算目标路径
                    rel_path = asset_file.relative_to(self.assets_dir)
                    target_path = self.docusaurus_dir / "assets" / rel_path

                    # 确保目标目录存在
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # 复制文件
                    shutil.copy2(asset_file, target_path)

        return success_count, failure_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Obsidian到Docusaurus转换工具")
    parser.add_argument("--obsidian-dir", "-o", required=True, help="Obsidian文档目录")
    parser.add_argument("--docusaurus-dir", "-d", required=True, help="Docusaurus文档目录")
    parser.add_argument("--assets-dir", "-a", help="资源文件目录，默认为obsidian_dir/assets")
    parser.add_argument("--file", "-f", help="指定要转换的单个文件（相对于obsidian-dir）")

    args = parser.parse_args()

    # 创建转换器
    converter = ObsidianDocusaurusConverter(
        args.obsidian_dir,
        args.docusaurus_dir,
        args.assets_dir,
    )

    # 构建文件映射
    converter.build_file_mapping()

    if args.file:
        # 转换单个文件
        file_path = Path(args.file)
        if converter.convert_file(file_path):
            logger.info(f"文件转换成功: {args.file}")
            return 0
        else:
            logger.error(f"文件转换失败: {args.file}")
            return 1
    else:
        # 转换所有文件
        success_count, failure_count = converter.convert_all_files()
        logger.info(f"转换完成: 成功 {success_count} 个，失败 {failure_count} 个")

        if failure_count > 0:
            return 1
        else:
            return 0


if __name__ == "__main__":
    sys.exit(main())
