"""
文件转换模块

处理单个或批量文件的转换
"""

from pathlib import Path
from typing import Tuple

from .base import logger
from .link_converter import LinkConverter


class FileConverter(LinkConverter):
    """文件转换器"""

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
            # 只跳过.obsidian配置目录和assets目录，而不是路径中包含这些名称的所有目录
            if (
                md_file.name == ".obsidian"
                or md_file.parent.name == ".obsidian"
                or md_file.parent.name == "assets"
            ):
                continue

            # 计算相对路径
            rel_path = md_file.relative_to(self.obsidian_dir)

            # 转换文件
            if self.convert_file(rel_path):
                success_count += 1
            else:
                failure_count += 1

        return success_count, failure_count
