#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script carefully edits the rule_command.py file by targeting exact strings.
"""


def main():
    # Define the file path
    file_path = "src/cli/commands/rule_command.py"

    # Read the file content as a single string
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Define the exact strings to replace
    old_string1 = "rule create <template_type> <n>  创建新规则"
    new_string1 = "rule create <template_type> <name>  创建新规则"

    old_string2 = "<n>                     规则名称"
    new_string2 = "<name>                     规则名称"

    # Make the replacements
    if old_string1 in content:
        content = content.replace(old_string1, new_string1)
        print(f"Replaced '{old_string1}' with '{new_string1}'")
    else:
        print(f"String '{old_string1}' not found.")

    if old_string2 in content:
        content = content.replace(old_string2, new_string2)
        print(f"Replaced '{old_string2}' with '{new_string2}'")
    else:
        print(f"String '{old_string2}' not found.")

    # Write the updated content back
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated parameter names in {file_path}")


if __name__ == "__main__":
    main()
