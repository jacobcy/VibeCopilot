#!/usr/bin/env python
"""
同步 AI 文档到 Cursor 规则

该脚本将 docs/ai 目录下的文档同步到 .cursor/rules 目录，
使 Cursor 能够加载这些规则作为上下文。
"""

import datetime
import glob
import os
import re
import sys
from pathlib import Path

import yaml

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent.resolve()
# AI 文档目录
AI_DOCS_DIR = ROOT_DIR / "docs" / "ai"
# Cursor 规则目录
CURSOR_RULES_DIR = ROOT_DIR / ".cursor" / "rules"

# 文件类型到规则名称的映射
RULE_NAME_MAPPING = {
    "rules": "rule",
    "prompts": "prompt",
    "context": "context",
    "references": "ref",
}


def ensure_dir(directory):
    """确保目录存在"""
    os.makedirs(directory, exist_ok=True)


def get_rule_name(file_path):
    """根据文件路径生成规则名称"""
    rel_path = Path(file_path).relative_to(AI_DOCS_DIR)
    # 获取第一级目录名
    top_dir = rel_path.parts[0] if len(rel_path.parts) > 0 else ""

    # 获取文件名（不含扩展名）
    stem = Path(file_path).stem

    # 生成规则名称前缀
    prefix = RULE_NAME_MAPPING.get(top_dir, "doc")

    # 构建规则名称
    return f"{prefix}_{stem}.mdc"


def sync_docs():
    """同步AI文档到Cursor规则"""
    print(f"正在同步AI文档到Cursor规则...")

    # 确保规则目录存在
    ensure_dir(CURSOR_RULES_DIR)

    # 记录已处理文件
    processed_files = []

    # 递归处理文档文件
    for doc_file in glob.glob(str(AI_DOCS_DIR / "**" / "*.md"), recursive=True):
        # 生成规则文件名
        rule_name = get_rule_name(doc_file)
        rule_path = CURSOR_RULES_DIR / rule_name

        # 记录处理的文件
        processed_files.append(rule_path)

        # 添加源文件信息的注释
        with open(doc_file, "r", encoding="utf-8") as src_file:
            content = src_file.read()

        # 添加元数据注释
        metadata = f"""<!--
自动同步于: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
源文件: {os.path.relpath(doc_file, ROOT_DIR)}
-->

"""

        # 写入规则文件
        with open(rule_path, "w", encoding="utf-8") as rule_file:
            rule_file.write(metadata + content)

        print(f"已同步: {os.path.relpath(doc_file, ROOT_DIR)} -> {rule_name}")

    # 删除不再存在的规则文件
    for rule_file in glob.glob(str(CURSOR_RULES_DIR / "*.mdc")):
        if Path(rule_file) not in processed_files and any(
            Path(rule_file).name.startswith(prefix) for prefix in RULE_NAME_MAPPING.values()
        ):
            os.remove(rule_file)
            print(f"已删除: {os.path.relpath(rule_file, ROOT_DIR)}")

    print(f"同步完成! 共同步 {len(processed_files)} 个文件")


def main():
    """同步AI文档到正确位置。"""
    try:
        sync_docs()
    except Exception as e:
        print(f"同步失败: {e}")
        sys.exit(1)


def process_file(file_path, output_dir):
    """处理单个文件并将其复制到目标位置。"""
    # ... existing code ...


def create_index(directory):
    """为指定目录创建索引文件。"""
    # ... existing code ...
    print(f"为 {directory} 创建了索引文件")
    # ... existing code ...


if __name__ == "__main__":
    main()
