#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script directly edits specific lines in rule_command.py to fix parameter names.
"""


def main():
    # Define the file path
    file_path = "src/cli/commands/rule_command.py"

    # Read all lines from the file
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Replace specific lines (using 0-based indexing)
    if len(lines) >= 56:  # Line 56 (0-based index 55)
        if "<n>" in lines[55]:
            lines[55] = lines[55].replace("<n>", "<name>")
            print(f"Updated line 56: {lines[55].strip()}")

    if len(lines) >= 67:  # Line 67 (0-based index 66)
        if "<n>" in lines[66]:
            lines[66] = lines[66].replace("<n>", "<name>")
            print(f"Updated line 67: {lines[66].strip()}")

    # Write the updated content back
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Updated parameter names in {file_path}")


if __name__ == "__main__":
    main()
