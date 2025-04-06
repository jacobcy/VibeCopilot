"""
Docusaurus配置生成器

负责生成Docusaurus侧边栏配置
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List

import yaml

logger = logging.getLogger(__name__)


def generate_docusaurus_sidebar(
    docusaurus_config: Dict[str, Any], templates_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    生成Docusaurus侧边栏配置

    Args:
        docusaurus_config: Docusaurus配置字典
        templates_config: 模板配置字典

    Returns:
        侧边栏配置字典
    """
    try:
        content_dir = Path(docusaurus_config["content_dir"])
        category_order = docusaurus_config["sidebar_category_order"]
        default_category = templates_config["default_category"]

        # 扫描文档目录
        categories = {}

        # 遍历所有markdown文件
        for md_file in content_dir.glob("**/*.md"):
            # 跳过索引文件
            if md_file.name == "_index.md":
                continue

            # 读取文件元数据
            category = _get_doc_category(md_file, default_category)

            if category not in categories:
                categories[category] = []

            # 计算相对路径
            rel_path = md_file.relative_to(content_dir)
            doc_id = str(rel_path.with_suffix(""))

            categories[category].append(
                {"type": "doc", "id": doc_id, "label": _get_doc_title(md_file)}
            )

        # 构建侧边栏配置
        sidebar = []

        # 先添加有序类别
        for category in category_order:
            if category in categories:
                sidebar.append(
                    {
                        "type": "category",
                        "label": category,
                        "items": sorted(categories[category], key=lambda x: x["label"]),
                    }
                )

                # 从分类中移除已处理的类别
                del categories[category]

        # 添加剩余类别
        for category, items in categories.items():
            sidebar.append(
                {
                    "type": "category",
                    "label": category,
                    "items": sorted(items, key=lambda x: x["label"]),
                }
            )

        logger.info(f"成功生成Docusaurus侧边栏配置")
        return {"sidebar": sidebar}

    except Exception as e:
        logger.error(f"生成侧边栏配置失败: {str(e)}")
        return {"sidebar": []}


def _get_doc_category(file_path: Path, default_category: str) -> str:
    """
    获取文档的分类

    Args:
        file_path: 文档文件路径
        default_category: 默认分类名称

    Returns:
        文档分类名称
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 尝试解析前置元数据
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                front_matter = content[3:end].strip()
                try:
                    metadata = yaml.safe_load(front_matter)
                    if metadata and "category" in metadata:
                        return metadata["category"]
                except yaml.YAMLError:
                    pass

        # 如果没有找到分类，使用父目录名称
        parent_dir = file_path.parent.name
        if parent_dir and parent_dir != ".":
            return parent_dir

        # 默认分类
        return default_category

    except Exception:
        return default_category


def _get_doc_title(file_path: Path) -> str:
    """
    获取文档的标题

    Args:
        file_path: 文档文件路径

    Returns:
        文档标题
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 尝试从前置元数据获取标题
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                front_matter = content[3:end].strip()
                try:
                    metadata = yaml.safe_load(front_matter)
                    if metadata and "title" in metadata:
                        return metadata["title"]
                except yaml.YAMLError:
                    pass

        # 尝试从一级标题获取
        title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()

        # 使用文件名作为标题
        return file_path.stem

    except Exception:
        return file_path.stem
