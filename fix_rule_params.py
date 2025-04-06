#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接使用Python打开文件并修改内容
"""

import os
import sys
import time


def main():
    # 定义文件路径
    file_path = os.path.join(os.getcwd(), "src/cli/commands/rule_command.py")
    print(f"准备修改文件: {file_path}")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return

    # 读取文件内容
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"文件大小: {len(content)} 字节")

    # 查找并替换
    old_text1 = "rule create <template_type> <n>  创建新规则"
    new_text1 = "rule create <template_type> <name>  创建新规则"

    old_text2 = "<n>                     规则名称"
    new_text2 = "<name>                     规则名称"

    # 执行替换
    content_new = content.replace(old_text1, new_text1)
    content_new = content_new.replace(old_text2, new_text2)

    # 检查是否有变化
    if content == content_new:
        print("警告: 没有进行任何替换！")

        # 显示相关内容段落进行检查
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "创建新规则" in line:
                print(f"行 {i+1}: {repr(line)}")
            if "规则名称" in line:
                print(f"行 {i+1}: {repr(line)}")
    else:
        print("检测到变化，准备写入文件...")

        # 写入新内容
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_new)

        print("文件已更新")

        # 显示更改后的内容
        lines = content_new.split("\n")
        for i, line in enumerate(lines):
            if "创建新规则" in line:
                print(f"行 {i+1} (更新后): {repr(line)}")
            if "规则名称" in line:
                print(f"行 {i+1} (更新后): {repr(line)}")


if __name__ == "__main__":
    main()
