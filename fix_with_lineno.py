#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
按行号直接修改文件内容
"""


def main():
    # 定义文件路径
    file_path = "src/cli/commands/rule_command.py"

    # 读取所有行
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"文件总行数: {len(lines)}")

    # 显示当前行内容
    print(f"行 56 (修改前): {lines[55]}")
    print(f"行 67 (修改前): {lines[66]}")

    # 直接修改特定行
    lines[55] = "            rule create <template_type> <name>  创建新规则\n"
    lines[66] = "            <name>                     规则名称\n"

    # 显示修改后内容
    print(f"行 56 (修改后): {lines[55]}")
    print(f"行 67 (修改后): {lines[66]}")

    # 写回文件
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"文件已更新: {file_path}")


if __name__ == "__main__":
    main()
