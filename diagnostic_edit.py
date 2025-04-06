#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script examines specific lines in rule_command.py for diagnostic purposes.
"""


def main():
    # Define the file path
    file_path = "src/cli/commands/rule_command.py"

    # Read all lines from the file
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Print the total number of lines
    print(f"Total lines in file: {len(lines)}")

    # Check specific lines
    for i, line_num in enumerate([55, 56, 66, 67]):
        if line_num < len(lines):
            print(f"Line {line_num+1}: {repr(lines[line_num])}")
        else:
            print(f"Line {line_num+1}: out of range")

    # Search for both <n> and <name> in the file
    n_occurrences = []
    name_occurrences = []

    for i, line in enumerate(lines):
        if "<n>" in line:
            n_occurrences.append((i + 1, line.strip()))
        if "<name>" in line:
            name_occurrences.append((i + 1, line.strip()))

    print(f"\nOccurrences of '<n>': {len(n_occurrences)}")
    for line_num, content in n_occurrences:
        print(f"  Line {line_num}: {content}")

    print(f"\nOccurrences of '<name>': {len(name_occurrences)}")
    for line_num, content in name_occurrences:
        print(f"  Line {line_num}: {content}")


if __name__ == "__main__":
    main()
