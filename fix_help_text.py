#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script fixes the parameter name in rule_command.py,
changing <n> to <name> for better clarity.
"""

import os
import re


def main():
    # Define the file path
    file_path = "src/cli/commands/rule_command.py"

    # Read the file content
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Define the help text pattern with a regex to match the entire help text section
    help_text_pattern = re.compile(r'def get_help\(cls\) -> str:\s+return """.*?"""', re.DOTALL)

    # Find the help text
    help_text_match = help_text_pattern.search(content)
    if not help_text_match:
        print("Help text not found in the file.")
        return

    help_text = help_text_match.group(0)

    # Replace occurrences in the help text
    updated_help_text = help_text.replace(
        "rule create <template_type> <n>  创建新规则", "rule create <template_type> <name>  创建新规则"
    )
    updated_help_text = updated_help_text.replace(
        "<n>                     规则名称", "<name>                     规则名称"
    )

    # Replace the help text in the content
    updated_content = content.replace(help_text, updated_help_text)

    # Write the updated content back
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Updated parameter names in {file_path}")


if __name__ == "__main__":
    main()
