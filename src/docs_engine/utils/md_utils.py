#!/usr/bin/env python
"""
Markdown 工具模块

提供用于检查和修复 Markdown 文档的工具函数，包括语法检查、链接修复等功能。
"""

import logging
import os
import re
from pathlib import Path


def fix_markdown_links(content, base_dir, file_path, logger=None):
    """修复Markdown文档中的链接

    Args:
        content: 文档内容
        base_dir: 基础目录路径
        file_path: 当前文件路径
        logger: 日志记录器

    Returns:
        修复后的文档内容
    """
    if logger is None:
        logger = logging.getLogger("md_utils")

    # 文件所在目录
    file_dir = os.path.dirname(file_path)

    # 修复相对链接 - 匹配Markdown链接[text](link)
    link_pattern = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

    def replace_link(match):
        text, link = match.groups()

        # 如果链接已经是绝对URL或以#开头(锚点)，无需处理
        if link.startswith(("http://", "https://", "#")):
            return match.group(0)

        # 移除链接中的锚点部分以便检查文件存在
        link_parts = link.split("#")
        link_path = link_parts[0]
        anchor = link_parts[1] if len(link_parts) > 1 else ""

        # 判断链接是否有文件扩展名
        if not os.path.splitext(link_path)[1]:
            # 没有扩展名，尝试添加.md
            link_path = f"{link_path}.md"

        # 计算目标文件的绝对路径
        if os.path.isabs(link_path):
            target_path = link_path
        else:
            target_path = os.path.normpath(os.path.join(file_dir, link_path))

        # 检查目标文件是否存在
        if not os.path.exists(target_path):
            # 尝试查找可能的匹配文件
            potential_files = find_potential_files(link_path, base_dir)
            if potential_files:
                # 使用第一个匹配项
                best_match = potential_files[0]
                # 计算相对路径
                rel_path = os.path.relpath(best_match, file_dir)
                # 重建链接
                new_link = f"{os.path.splitext(rel_path)[0]}"
                if anchor:
                    new_link = f"{new_link}#{anchor}"

                logger.info(f"在 {file_path} 中修复链接: [{text}]({link}) -> [{text}]({new_link})")
                return f"[{text}]({new_link})"
            else:
                logger.warning(f"在 {file_path} 中找不到匹配的文件: {link}")

        return match.group(0)

    # 修复链接
    fixed_content = link_pattern.sub(replace_link, content)

    return fixed_content


def find_potential_files(link_path, base_dir):
    """查找可能匹配的文件

    Args:
        link_path: 链接路径
        base_dir: 基础目录

    Returns:
        可能匹配的文件列表
    """
    # 获取不带扩展名的文件名
    base_name = os.path.basename(link_path)
    file_name = os.path.splitext(base_name)[0]

    # 在所有文档目录中查找匹配的文件
    matches = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".md") and os.path.splitext(file)[0] == file_name:
                matches.append(os.path.join(root, file))

    return matches


def fix_mdx_syntax(content, file_path, logger=None):
    """修复MDX语法错误

    Args:
        content: 文档内容
        file_path: 当前文件路径
        logger: 日志记录器

    Returns:
        修复后的文档内容
    """
    if logger is None:
        logger = logging.getLogger("md_utils")

    # 修复代码块中常见的MDX语法错误
    fixed_content = content

    # 1. 修复没有闭合的Tabs组件
    if "<Tabs>" in fixed_content and "</Tabs>" not in fixed_content:
        logger.info(f"在 {file_path} 中修复未闭合的Tabs标签")
        fixed_content = fixed_content.replace("<Tabs>", "<Tabs>\n")
        # 查找位置在末尾添加闭合标签
        last_tab_item_end = fixed_content.rfind("</TabItem>")
        if last_tab_item_end > 0:
            fixed_content = (
                fixed_content[: last_tab_item_end + 10]
                + "\n</Tabs>"
                + fixed_content[last_tab_item_end + 10 :]
            )

    # 2. 修复数字开头的JSX标签
    jsx_number_tag_pattern = re.compile(r"<(\d+)([:\s])")
    if jsx_number_tag_pattern.search(fixed_content):
        logger.info(f"在 {file_path} 中修复数字开头的JSX标签")
        fixed_content = jsx_number_tag_pattern.sub(r"&lt;\1\2", fixed_content)

    # 3. 修复不正确的结束标签
    wrong_closing_tag_pattern = re.compile(r"</([\w-]+):([\w-]+)>")
    if wrong_closing_tag_pattern.search(fixed_content):
        logger.info(f"在 {file_path} 中修复不正确的结束标签")
        fixed_content = wrong_closing_tag_pattern.sub(r"</\1\2>", fixed_content)

    return fixed_content


def fix_document(file_path, base_dir=None, logger=None):
    """修复Markdown文档

    Args:
        file_path: 文件路径
        base_dir: 基础目录路径，如果为None则使用文件所在目录
        logger: 日志记录器

    Returns:
        是否成功修复
    """
    if logger is None:
        logger = logging.getLogger("md_utils")

    if base_dir is None:
        base_dir = os.path.dirname(file_path)

    try:
        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # 修复链接
        fixed_content = fix_markdown_links(content, base_dir, file_path, logger)

        # 修复MDX语法
        fixed_content = fix_mdx_syntax(fixed_content, file_path, logger)

        # 如果内容有变更，写回文件
        if fixed_content != content:
            logger.info(f"修复文件: {file_path}")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(fixed_content)
            return True
        else:
            logger.debug(f"文件无需修复: {file_path}")
            return False
    except Exception as e:
        logger.error(f"修复文件时出错 {file_path}: {str(e)}")
        return False


def batch_fix_documents(directory, logger=None):
    """批量修复目录中的Markdown文档

    Args:
        directory: 目录路径
        logger: 日志记录器

    Returns:
        修复的文件数量
    """
    if logger is None:
        logger = logging.getLogger("md_utils")

    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                if fix_document(file_path, directory, logger):
                    count += 1

    return count


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("md_utils")

    # 测试代码
    import sys

    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isdir(path):
            count = batch_fix_documents(path, logger)
            logger.info(f"已修复 {count} 个文件")
        elif os.path.isfile(path):
            success = fix_document(path, logger=logger)
            logger.info(f"文件修复{'成功' if success else '失败'}")
        else:
            logger.error(f"无效的路径: {path}")
    else:
        logger.error("请指定要修复的文件或目录路径")
