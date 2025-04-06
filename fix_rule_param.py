#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script fixes the parameter name in rule_command.py,
changing <n> to <name> for better clarity.
"""

import os


def main():
    # Define the file path
    file_path = "src/cli/commands/rule_command.py"

    # Read the file content
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace occurrences
    content = content.replace(
        "rule create <template_type> <n>", "rule create <template_type> <name>"
    )
    content = content.replace("<n>                     规则名称", "<name>                     规则名称")

    # Write the updated content back
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated parameter names in {file_path}")


if __name__ == "__main__":
    main()
