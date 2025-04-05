"""
转换器工具函数。
"""

import re
from typing import Tuple


def split_frontmatter(content: str) -> Tuple[str, str]:
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
