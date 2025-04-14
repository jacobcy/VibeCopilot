#!/usr/bin/env python3
import os
import re
from pathlib import Path

import yaml


def filter_command_data(data):
    if not isinstance(data, dict):
        return data

    filtered = {}
    for key, value in data.items():
        if key in ["commands", "subcommands", "values"]:
            if isinstance(value, dict):
                filtered[key] = {k: filter_command_data(v) for k, v in value.items()}
            else:
                filtered[key] = value
    return filtered


def format_yaml_for_markdown(yaml_content):
    return f"""<!-- BEGIN_COMMAND_YAML -->
```yaml
{yaml_content}
```
<!-- END_COMMAND_YAML -->"""


def update_mdc_file(mdc_path, yaml_content):
    if not mdc_path.exists():
        mdc_path.write_text(format_yaml_for_markdown(yaml_content))
        return

    content = mdc_path.read_text()
    pattern = r"<!-- BEGIN_COMMAND_YAML -->.*?<!-- END_COMMAND_YAML -->"
    replacement = format_yaml_for_markdown(yaml_content)

    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    else:
        new_content = content + "\n\n" + replacement

    mdc_path.write_text(new_content)


def merge_command_files():
    base_dir = Path("/Users/jacobcy/Public/VibeCopilot/src/health/config/commands")
    rules_dir = Path("/Users/jacobcy/Public/VibeCopilot/.cursor/rules/command-rules")

    # 确保目标目录存在
    rules_dir.mkdir(parents=True, exist_ok=True)

    # 用于存储分组命令
    command_groups = {}

    # 读取并过滤所有命令文件
    for yaml_file in base_dir.glob("*_commands.yaml"):
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data or "commands" not in data:
                continue

            filtered_data = filter_command_data(data)
            base_name = yaml_file.stem

            # 特殊处理flow相关命令
            if base_name in ["flow_commands", "flow_session_commands"]:
                group_name = "flow"
            else:
                group_name = base_name.split("_")[0]

            if group_name not in command_groups:
                command_groups[group_name] = {"commands": {}}

            command_groups[group_name]["commands"].update(filtered_data["commands"])

    # 写入对应的.mdc文件
    for group_name, commands in command_groups.items():
        mdc_path = rules_dir / f"{group_name}-commands.mdc"
        yaml_content = yaml.dump(commands, allow_unicode=True, sort_keys=False)
        update_mdc_file(mdc_path, yaml_content)


if __name__ == "__main__":
    merge_command_files()
