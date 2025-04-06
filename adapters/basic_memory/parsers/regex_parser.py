"""
正则表达式解析器
使用基本的正则表达式从Markdown文档中提取实体和关系
"""

import re
from pathlib import Path

import frontmatter


def parse_with_regex(file_path):
    """使用正则表达式解析文档

    Args:
        file_path: 文件路径

    Returns:
        Dict: 解析结果
    """
    print("使用基础正则表达式解析...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析front matter
    post = frontmatter.loads(content)
    metadata = dict(post.metadata) if post.metadata else {}
    content_text = post.content

    # 提取标题
    title_match = re.search(r"^#\s+(.*?)$", content_text, re.MULTILINE)
    title = title_match.group(1) if title_match else Path(file_path).stem

    # 提取Wiki链接作为实体
    wiki_links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content_text)

    # 提取标准Markdown链接
    md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content_text)

    # 提取标题作为实体
    headings = re.findall(r"^##\s+(.*?)$", content_text, re.MULTILINE)

    # 提取标签
    tags = []
    if "tags" in metadata:
        if isinstance(metadata["tags"], list):
            tags.extend(metadata["tags"])
        elif isinstance(metadata["tags"], str):
            tags.append(metadata["tags"])

    # 从内容中提取#标签
    hash_tags = re.findall(r"#(\w+)", content_text)
    tags.extend(hash_tags)

    # 构建实体列表
    entities = []

    # 添加文档本身作为实体
    entities.append({"name": title, "type": "document", "description": "主文档"})

    # 添加Wiki链接作为实体
    for link in wiki_links:
        entities.append({"name": link, "type": "linked_document", "description": "通过Wiki链接引用的文档"})

    # 添加标题作为实体
    for heading in headings:
        entities.append({"name": heading, "type": "section", "description": "文档章节"})

    # 构建关系
    relations = []

    # 添加文档到Wiki链接的关系
    for link in wiki_links:
        relations.append({"source": title, "target": link, "type": "references"})

    # 添加文档到章节的关系
    for heading in headings:
        relations.append({"source": title, "target": heading, "type": "contains"})

    result = {
        "document_type": metadata.get("type", "unknown"),
        "main_topic": title,
        "entities": entities,
        "relations": relations,
        "observations": [],
        "tags": list(set(tags)),
    }

    return result
