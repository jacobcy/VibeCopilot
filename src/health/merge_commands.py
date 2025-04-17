#!/usr/bin/env python3
import os
import re
from pathlib import Path

import yaml


# Helper function to safely get description
def get_desc(data_dict, key, default=""):
    if isinstance(data_dict, dict):
        return data_dict.get(key, {}).get("description", default)
    return default


# Modified filter_command_data
def filter_command_data(data):
    """
    过滤命令数据，提取命令结构（区分arguments和options）并准备注释内容

    Args:
        data: 原始命令数据

    Returns:
        dict: 过滤后的命令数据 (包含 arguments 和 options)
        dict: 命令、参数和选项的描述
    """
    if not isinstance(data, dict):
        return data, {}

    filtered = {}
    descriptions = {}

    for key, value in data.items():
        if key == "commands":
            if isinstance(value, dict):
                filtered[key] = {}
                descriptions[key] = {}  # For command descriptions

                for cmd_name, cmd_data in value.items():
                    # Initialize command entry in filtered data and descriptions
                    filtered[key][cmd_name] = {"arguments": {}, "options": {}}
                    descriptions[key][cmd_name] = {"description": cmd_data.get("description", ""), "arguments": {}, "options": {}}

                    # Process Arguments
                    if "arguments" in cmd_data and isinstance(cmd_data["arguments"], list):
                        for arg_data in cmd_data["arguments"]:
                            if isinstance(arg_data, dict) and "name" in arg_data:
                                arg_name = arg_data["name"]
                                filtered[key][cmd_name]["arguments"][arg_name] = {}  # Store only name
                                descriptions[key][cmd_name]["arguments"][arg_name] = arg_data.get("description", "")

                    # Process Options (formerly subcommands in this context)
                    if "options" in cmd_data and isinstance(cmd_data["options"], dict):
                        for opt_name, opt_data in cmd_data["options"].items():
                            filtered[key][cmd_name]["options"][opt_name] = {}  # Store only name
                            descriptions[key][cmd_name]["options"][opt_name] = opt_data.get("description", "")

            else:
                # Keep non-dict command structures as is? Or raise error?
                # For now, keep as is, assuming valid structure upstream.
                filtered[key] = value
        # We are only interested in the top-level 'commands' key for this structure
        # Other keys like 'group_config' are ignored for the rule file.

    return filtered, descriptions


# Modified format_yaml_with_comments
def format_yaml_with_comments(yaml_obj, descriptions, verbose=False):
    """
    将过滤后的命令数据转换为带注释的YAML文本 (arguments/options structure)

    Args:
        yaml_obj: 过滤后的YAML数据对象 (来自 filter_command_data)
        descriptions: 描述信息字典 (来自 filter_command_data)
        verbose: 是否显示详细信息

    Returns:
        str: 带注释的YAML文本
    """
    yaml_lines = []
    yaml_lines.append("commands:")

    if verbose:
        print("正在生成带注释的YAML (新结构)：")

    for cmd_name, cmd_data in yaml_obj.get("commands", {}).items():
        cmd_desc = descriptions.get("commands", {}).get(cmd_name, {}).get("description", "")
        if cmd_desc:
            yaml_lines.append(f"  {cmd_name}: # {cmd_desc}")
            if verbose:
                print(f"  添加命令: {cmd_name} # {cmd_desc}")
        else:
            yaml_lines.append(f"  {cmd_name}:")
            if verbose:
                print(f"  添加命令: {cmd_name}")

        # Add Arguments
        if cmd_data.get("arguments"):
            yaml_lines.append("    arguments:")
            arg_descs = descriptions.get("commands", {}).get(cmd_name, {}).get("arguments", {})
            for arg_name in cmd_data["arguments"]:
                arg_desc = arg_descs.get(arg_name, "")
                if arg_desc:
                    yaml_lines.append(f"      {arg_name}: # {arg_desc}")
                    if verbose:
                        print(f"      添加参数: {arg_name} # {arg_desc}")
                else:
                    yaml_lines.append(f"      {arg_name}:")
                    if verbose:
                        print(f"      添加参数: {arg_name}")

        # Add Options
        if cmd_data.get("options"):
            yaml_lines.append("    options:")
            opt_descs = descriptions.get("commands", {}).get(cmd_name, {}).get("options", {})
            for opt_name in cmd_data["options"]:
                opt_desc = opt_descs.get(opt_name, "")
                if opt_desc:
                    yaml_lines.append(f"      {opt_name}: # {opt_desc}")
                    if verbose:
                        print(f"      添加选项: {opt_name} # {opt_desc}")
                else:
                    yaml_lines.append(f"      {opt_name}:")
                    if verbose:
                        print(f"      添加选项: {opt_name}")

    yaml_content = "\n".join(yaml_lines)

    if verbose:
        print(f"生成了 {len(yaml_lines)} 行 YAML 内容 (新结构)")

    return yaml_content


def format_yaml_for_markdown(yaml_content):
    return f"""<!-- BEGIN_COMMAND_YAML -->
```yaml
{yaml_content}
```
<!-- END_COMMAND_YAML -->"""


def update_mdc_file(mdc_path, yaml_content, verbose=False, force=False):
    """
    更新MDC文件中的YAML内容，确保只替换指定标签之间的部分。

    Args:
        mdc_path: MDC文件路径
        yaml_content: 新的YAML内容 (不包含标签)
        verbose: 是否显示详细信息
    """
    if verbose:
        print(f"准备更新文件: {mdc_path}")

    start_tag = "<!-- BEGIN_COMMAND_YAML -->"
    end_tag = "<!-- END_COMMAND_YAML -->"
    new_yaml_block_with_tags = format_yaml_for_markdown(yaml_content)

    header = ""
    footer = ""
    content = ""

    if mdc_path.exists():
        content = mdc_path.read_text(encoding="utf-8")
        if verbose:
            print(f"读取现有文件，长度: {len(content)} 字节")

        start_index = content.find(start_tag)
        end_index = -1
        if start_index != -1:
            # Search for end tag *after* the start tag
            end_index = content.find(end_tag, start_index + len(start_tag))

        if start_index != -1 and end_index != -1:
            # Both tags found, extract header and footer
            if verbose:
                print("找到现有YAML块，准备替换")
            header = content[:start_index]
            footer = content[end_index + len(end_tag) :]
            # Ensure header ends with appropriate newlines if not empty
            if header and not header.endswith("\n\n"):
                if header.endswith("\n"):
                    header += "\n"
                else:
                    header += "\n\n"
            # Ensure footer starts with appropriate newlines if not empty
            if footer and not footer.startswith("\n"):
                # Check if header already added double newline
                if header.endswith("\n\n"):
                    # Need to be careful not to add triple newline
                    pass  # Header already provides separation
                elif header.endswith("\n"):
                    footer = "\n" + footer
                else:  # header is empty or doesn't end with newline
                    footer = "\n\n" + footer

            new_content = header + new_yaml_block_with_tags + footer
        else:
            # Tags not found or incomplete, treat existing content as header
            if verbose:
                print("未找到完整的YAML块，将添加到文件末尾（或覆盖，取决于原始逻辑）")
            # Treat existing content as header, ensure separation
            header = content.rstrip() + "\n\n" if content else ""
            new_content = header + new_yaml_block_with_tags
            footer = ""  # No footer if appending
    else:
        # File does not exist, create new with just the block
        if verbose:
            print(f"文件不存在，创建新文件")
        new_content = new_yaml_block_with_tags
        # Header and footer remain empty

    # Write the reconstructed content
    if verbose:
        print(f"写入更新后的内容，长度: {len(new_content)} 字节")
        # Optional: Log parts for debugging
        # print(f"\n--- Header ({len(header)} bytes) ---\n{header[:100]}...")
        # print(f"\n--- New Block ({len(new_yaml_block_with_tags)} bytes) ---\n{new_yaml_block_with_tags[:200]}...")
        # print(f"\n--- Footer ({len(footer)} bytes) ---\n{footer[:100]}...")

    mdc_path.write_text(new_content, encoding="utf-8")


def merge_command_files(verbose=False, force=False):
    """
    将命令配置文件合并到规则目录中

    Args:
        verbose: 是否显示详细信息
        force: (已弃用，但保留以兼容旧调用) 是否强制重写规则文件

    Returns:
        dict: 包含处理结果的字典，包括成功和失败的文件列表
    """
    # 获取项目根目录
    project_root = Path(os.getcwd())
    # 源目录: 命令配置文件目录
    base_dir = project_root / "src" / "health" / "config" / "commands"
    # 目标目录: 规则目录
    rules_dir = project_root / ".cursor" / "rules" / "command-rules"

    if verbose:
        print(f"命令配置源目录: {base_dir}")
        print(f"规则目标目录: {rules_dir}")
        # if force: # No longer relevant for the core logic
        #     print("强制重写模式已启用")

    # 确保目标目录存在
    rules_dir.mkdir(parents=True, exist_ok=True)

    # 用于存储分组命令
    command_groups = {}
    description_groups = {}

    # 处理结果
    result = {"success": [], "failed": [], "total_files": 0, "total_commands": 0}

    # 检查源目录是否存在
    if not base_dir.exists():
        print(f"错误: 命令配置目录不存在: {base_dir}")
        result["failed"].append({"path": str(base_dir), "error": "目录不存在"})
        return result

    # 读取并过滤所有命令文件
    yaml_files = list(base_dir.glob("*_commands.yaml"))  # Specific pattern
    # Exclude config.yaml
    yaml_files = [f for f in yaml_files if f.name != "config.yaml"]
    result["total_files"] = len(yaml_files)

    if verbose:
        print(f"发现 {len(yaml_files)} 个命令配置文件")

    for yaml_file in yaml_files:
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data or "commands" not in data:
                    if verbose:
                        print(f"警告: 文件 {yaml_file} 中没有找到有效的命令配置")
                    # Still add to failed? Or just skip? Let's skip silently for now.
                    # result["failed"].append({"path": str(yaml_file), "error": "没有有效的命令配置"})
                    continue

                filtered_data, descriptions = filter_command_data(data)  # Use modified function
                base_name = yaml_file.stem

                # 记录命令数量
                result["total_commands"] += len(filtered_data.get("commands", {}))

                # 特殊处理flow相关命令
                if base_name in ["flow_commands", "flow_session_commands"]:
                    group_name = "flow"
                else:
                    group_name = base_name.split("_")[0]

                if group_name not in command_groups:
                    command_groups[group_name] = {"commands": {}}
                    description_groups[group_name] = {"commands": {}}

                # Merge commands data correctly
                existing_commands = command_groups[group_name].get("commands", {})
                new_commands = filtered_data.get("commands", {})
                existing_commands.update(new_commands)  # Merge new commands into existing
                command_groups[group_name]["commands"] = existing_commands

                # Merge descriptions correctly
                existing_descs = description_groups[group_name].get("commands", {})
                new_descs = descriptions.get("commands", {})
                existing_descs.update(new_descs)
                description_groups[group_name]["commands"] = existing_descs

                if verbose:
                    print(f"处理文件: {yaml_file} -> 命令组: {group_name}")

                result["success"].append({"path": str(yaml_file), "group": group_name})
        except Exception as e:
            if verbose:
                print(f"处理文件 {yaml_file} 时出错: {str(e)}")
            result["failed"].append({"path": str(yaml_file), "error": str(e)})

    # 写入对应的.mdc文件
    for group_name, commands in command_groups.items():
        try:
            mdc_path = rules_dir / f"{group_name}-commands.mdc"

            # 转换为带注释的YAML格式 (use modified function)
            yaml_content = format_yaml_with_comments(commands, description_groups[group_name], verbose)

            # Use the rewritten update function (force parameter is now ignored internally)
            update_mdc_file(mdc_path, yaml_content, verbose=verbose)

            if verbose:
                print(f"已更新规则文件: {mdc_path}")
        except Exception as e:
            if verbose:
                print(f"更新规则文件 {mdc_path} 时出错: {str(e)}")
            result["failed"].append({"path": str(mdc_path), "error": str(e)})

    return result


if __name__ == "__main__":
    # Example usage: python src/health/merge_commands.py --verbose
    import argparse

    parser = argparse.ArgumentParser(description="Merge command configs into rule files.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output.")
    # Keep force for backward compatibility, but it's ignored by the new update_mdc_file
    parser.add_argument("--force", action="store_true", help="(Deprecated) Force rewrite rule files.")
    args = parser.parse_args()

    result = merge_command_files(verbose=args.verbose, force=args.force)
    print(f"\n处理完成: 成功 {len(result['success'])} 个文件, 失败 {len(result['failed'])} 个文件")
    if result["failed"]:
        print("失败详情:")
        for fail in result["failed"]:
            print(f"- {fail['path']}: {fail['error']}")
