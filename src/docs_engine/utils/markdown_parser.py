"""
Markdown解析器模块

提供Markdown文档与块之间的转换功能
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from src.models.db.docs_engine import BlockType


def parse_markdown_to_blocks(content: str) -> List[Dict[str, Any]]:
    """解析Markdown内容为块结构

    Args:
        content: Markdown内容

    Returns:
        块数据字典列表
    """
    blocks = []
    lines = content.split("\n")

    current_block = {"type": BlockType.TEXT.value, "content": "", "metadata": {}}
    in_code_block = False

    for line in lines:
        # 处理代码块
        if line.startswith("```"):
            if in_code_block:
                # 结束代码块
                current_block["content"] += line + "\n"
                blocks.append(current_block)
                current_block = {"type": BlockType.TEXT.value, "content": "", "metadata": {}}
                in_code_block = False
            else:
                # 开始代码块，保存之前的文本块
                if current_block["content"].strip():
                    blocks.append(current_block)

                # 开始新代码块
                in_code_block = True
                current_block = {
                    "type": BlockType.CODE.value,
                    "content": line + "\n",
                    "metadata": {},
                }

                # 提取语言信息
                language_match = re.match(r"```(\w+)", line)
                if language_match:
                    current_block["metadata"]["language"] = language_match.group(1)

        # 处理标题
        elif not in_code_block and re.match(r"^#{1,6} ", line):
            # 保存之前的块
            if current_block["content"].strip():
                blocks.append(current_block)

            # 创建标题块
            level = len(re.match(r"^(#+) ", line).group(1))
            blocks.append(
                {
                    "type": BlockType.HEADING.value,
                    "content": line.lstrip("#").strip(),
                    "metadata": {"level": level},
                }
            )

            # 开始新文本块
            current_block = {"type": BlockType.TEXT.value, "content": "", "metadata": {}}

        # 普通文本行
        else:
            current_block["content"] += line + "\n"

    # 处理最后一个块
    if current_block["content"].strip():
        blocks.append(current_block)

    # 设置顺序
    for i, block in enumerate(blocks):
        block["order"] = i

    return blocks


def render_blocks_to_markdown(blocks: List[Dict[str, Any]]) -> str:
    """将块列表渲染为Markdown内容

    Args:
        blocks: 块数据字典列表

    Returns:
        Markdown内容
    """
    # 按order排序
    sorted_blocks = sorted(blocks, key=lambda b: b.get("order", 0))

    content = ""

    for block in sorted_blocks:
        block_type = block.get("type", BlockType.TEXT.value)
        block_content = block.get("content", "")
        metadata = block.get("metadata", {})

        if block_type == BlockType.HEADING.value:
            # 渲染标题
            level = metadata.get("level", 1)
            content += f"{'#' * level} {block_content}\n\n"

        elif block_type == BlockType.CODE.value:
            # 渲染代码块
            language = metadata.get("language", "")

            # 检查内容是否已经包含代码块标记
            if block_content.startswith("```") and block_content.endswith("```\n"):
                content += block_content + "\n"
            else:
                content += f"```{language}\n{block_content}```\n\n"

        else:  # 默认为文本块
            content += block_content + "\n"

    return content


def process_markdown_links(content: str, converter: Optional[callable] = None) -> str:
    """处理Markdown内容中的链接

    如果提供了转换器函数，将使用它来转换链接格式

    Args:
        content: Markdown内容
        converter: 链接转换函数，接收匹配对象，返回替换字符串

    Returns:
        处理后的Markdown内容
    """
    if not converter:
        return content

    # 匹配 [[doc-id]] 或 [[doc-id#block-id]] 或 [[doc-id|显示文本]]
    pattern = r"\[\[(doc-[a-zA-Z0-9-]+)(?:#(blk-[a-zA-Z0-9-]+))?(?:\|(.*?))?\]\]"

    # 使用转换器替换链接
    return re.sub(pattern, converter, content)


def extract_metadata(content: str) -> Tuple[Dict[str, Any], str]:
    """从Markdown内容中提取YAML前置元数据

    Args:
        content: Markdown内容

    Returns:
        (元数据字典, 剩余内容)元组
    """
    import yaml

    # 匹配YAML前置元数据
    pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.search(pattern, content, re.DOTALL)

    if match:
        # 提取并解析YAML
        yaml_text = match.group(1)
        try:
            metadata = yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError:
            metadata = {}

        # 移除前置元数据
        remaining_content = content[match.end() :]

        return metadata, remaining_content

    # 没有前置元数据
    return {}, content
