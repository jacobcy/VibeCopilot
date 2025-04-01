"""
Obsidian导出模块
提供将实体导出到Obsidian vault的功能
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

import yaml


class ObsidianExporter:
    """Obsidian导出器，提供导出到Obsidian vault的功能"""

    def __init__(self, vault_path: str):
        """初始化导出器

        Args:
            vault_path: Obsidian vault路径
        """
        self.vault_path = os.path.expanduser(vault_path)
        self.setup_vault()

    def setup_vault(self) -> None:
        """设置Obsidian vault目录"""
        if os.path.exists(self.vault_path):
            # 如果目录存在，先清空它
            for root, dirs, files in os.walk(self.vault_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        else:
            # 创建新目录
            os.makedirs(self.vault_path)

    def export_document(
        self,
        original_path: Path,
        source_dir: Path,
        metadata: Dict,
        observations: List[Tuple[str, str]],
        relations: List[Tuple[str, str]],
    ) -> None:
        """导出文档到Obsidian

        Args:
            original_path: 原始文件路径
            source_dir: 源目录
            metadata: 元数据
            observations: 观察列表，每个观察为(内容, 类型)
            relations: 关系列表，每个关系为(目标标题, 关系类型)
        """
        try:
            # 确保目标目录存在
            rel_path = original_path.relative_to(source_dir)
            target_path = Path(self.vault_path) / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 构建文档内容
            content = []

            # 添加front matter
            if metadata:
                content.append("---")
                content.append(yaml.dump(metadata))
                content.append("---\n")

            # 添加观察内容
            for obs_content, _ in observations:
                content.append(obs_content)
                content.append("")  # 空行分隔

            # 添加反向链接
            if relations:
                content.append("\n## 相关链接")
                for target_title, rel_type in relations:
                    content.append(f"- [[{target_title}]] ({rel_type})")

            # 写入文件
            target_path.write_text("\n".join(content), encoding="utf-8")
            print(f"已导出: {target_path}")

        except Exception as e:
            print(f"警告: 导出文件时出错: {str(e)}")
