#!/usr/bin/env python3
import os
import re
from pathlib import Path

import yaml


def filter_command_data(data):
    """
    过滤命令数据，提取命令结构并准备注释内容

    Args:
        data: 原始命令数据

    Returns:
        dict: 过滤后的命令数据
        dict: 命令和参数的描述，用于后续添加注释
    """
    if not isinstance(data, dict):
        return data, {}

    filtered = {}
    descriptions = {}  # 存储描述信息，用于后面作为注释添加

    for key, value in data.items():
        # 处理主命令结构
        if key == "commands":
            if isinstance(value, dict):
                filtered[key] = {}
                descriptions[key] = {}

                # 处理每个命令
                for cmd_name, cmd_data in value.items():
                    filtered[key][cmd_name] = {}
                    descriptions[key][cmd_name] = cmd_data.get("description", "")

                    # 处理子命令
                    if "subcommands" in cmd_data and isinstance(cmd_data["subcommands"], dict):
                        filtered[key][cmd_name]["subcommands"] = {}
                        descriptions[key][cmd_name + ".subcommands"] = {}

                        for subcmd_name, subcmd_data in cmd_data["subcommands"].items():
                            filtered[key][cmd_name]["subcommands"][subcmd_name] = {}
                            descriptions[key][cmd_name + ".subcommands"][subcmd_name] = subcmd_data.get("description", "")

                            # 保留值列表
                            if "values" in subcmd_data:
                                filtered[key][cmd_name]["subcommands"][subcmd_name]["values"] = subcmd_data["values"]

                            # 保留类型信息
                            if "type" in subcmd_data:
                                filtered[key][cmd_name]["subcommands"][subcmd_name]["type"] = subcmd_data["type"]

                    # 保留值列表
                    if "values" in cmd_data:
                        filtered[key][cmd_name]["values"] = cmd_data["values"]
            else:
                filtered[key] = value
        # 保留其他关键结构
        elif key in ["subcommands", "values"]:
            if isinstance(value, dict):
                filtered[key] = {k: filter_command_data(v)[0] for k, v in value.items()}
            else:
                filtered[key] = value

    return filtered, descriptions


def format_yaml_with_comments(yaml_obj, descriptions, verbose=False):
    """
    将YAML对象转换为带注释的YAML文本

    Args:
        yaml_obj: YAML数据对象
        descriptions: 描述信息字典
        verbose: 是否显示详细信息

    Returns:
        str: 带注释的YAML文本
    """
    # 生成YAML文本
    yaml_lines = []
    yaml_lines.append("commands:")

    if verbose:
        print("正在生成带注释的YAML：")

    # 添加命令及其描述
    for cmd_name, cmd_data in yaml_obj.get("commands", {}).items():
        desc = descriptions.get("commands", {}).get(cmd_name, "")
        if desc:
            yaml_lines.append(f"  {cmd_name}: # {desc}")
            if verbose:
                print(f"  添加命令: {cmd_name} # {desc}")
        else:
            yaml_lines.append(f"  {cmd_name}:")
            if verbose:
                print(f"  添加命令: {cmd_name}")

        # 添加子命令及其描述
        if "subcommands" in cmd_data and isinstance(cmd_data["subcommands"], dict):
            yaml_lines.append("    subcommands:")
            subcmd_key = cmd_name + ".subcommands"
            for subcmd_name, subcmd_data in cmd_data["subcommands"].items():
                subcmd_desc = descriptions.get("commands", {}).get(subcmd_key, {}).get(subcmd_name, "")
                if subcmd_desc:
                    yaml_lines.append(f"      {subcmd_name}: # {subcmd_desc}")
                    if verbose:
                        print(f"    添加子命令: {subcmd_name} # {subcmd_desc}")
                else:
                    yaml_lines.append(f"      {subcmd_name}:")
                    if verbose:
                        print(f"    添加子命令: {subcmd_name}")

                # 添加值列表
                if "values" in subcmd_data and isinstance(subcmd_data["values"], list):
                    yaml_lines.append("        values:")
                    for val in subcmd_data["values"]:
                        yaml_lines.append(f"        - {val}")

                # 添加类型
                if "type" in subcmd_data:
                    yaml_lines.append(f"        type: {subcmd_data['type']}")

        # 添加命令的值列表
        if "values" in cmd_data and isinstance(cmd_data["values"], list):
            yaml_lines.append("    values:")
            for val in cmd_data["values"]:
                yaml_lines.append(f"    - {val}")

    yaml_content = "\n".join(yaml_lines)

    if verbose:
        print(f"生成了{len(yaml_lines)}行YAML内容")

    return yaml_content


def format_yaml_for_markdown(yaml_content):
    return f"""<!-- BEGIN_COMMAND_YAML -->
```yaml
{yaml_content}
```
<!-- END_COMMAND_YAML -->"""


def update_mdc_file(mdc_path, yaml_content, verbose=False, force=False):
    """
    更新MDC文件中的YAML内容

    Args:
        mdc_path: MDC文件路径
        yaml_content: 新的YAML内容
        verbose: 是否显示详细信息
        force: 是否强制重写整个文件
    """
    if verbose:
        print(f"准备更新文件: {mdc_path}")

    # 如果文件不存在或者强制重写
    if not mdc_path.exists() or force:
        if verbose:
            if not mdc_path.exists():
                print(f"文件不存在，创建新文件")
            else:
                print(f"强制重写文件")

        # 为了保留文件头信息和其他内容，如果文件存在且是重写模式，我们先抽取文件头
        file_header = ""
        if mdc_path.exists() and force:
            content = mdc_path.read_text(encoding="utf-8")
            # 寻找yaml块开始标记的位置
            yaml_start = content.find("<!-- BEGIN_COMMAND_YAML -->")
            if yaml_start > 0:
                file_header = content[:yaml_start].rstrip() + "\n\n"
            else:
                file_header = content

        # 写入文件
        mdc_path.write_text(file_header + format_yaml_for_markdown(yaml_content), encoding="utf-8")
        return

    # 读取现有文件内容
    content = mdc_path.read_text(encoding="utf-8")
    if verbose:
        print(f"读取文件，长度: {len(content)} 字节")

    # 查找YAML块
    pattern = r"<!-- BEGIN_COMMAND_YAML -->.*?<!-- END_COMMAND_YAML -->"
    yaml_block = format_yaml_for_markdown(yaml_content)

    if verbose:
        print(f"新YAML块长度: {len(yaml_block)} 字节")

    # 如果找到YAML块，替换它
    if re.search(pattern, content, re.DOTALL):
        if verbose:
            print("找到现有YAML块，进行替换")
        new_content = re.sub(pattern, yaml_block, content, flags=re.DOTALL)
    else:
        # 如果没有找到，添加到文件末尾
        if verbose:
            print("未找到YAML块，添加到文件末尾")
        new_content = content + "\n\n" + yaml_block

    # 写入更新后的内容
    if verbose:
        print(f"写入更新后的内容，长度: {len(new_content)} 字节")

    # 打印更改前后的YAML部分，便于调试
    if verbose:
        print("\n--- 原YAML块 ---")
        yaml_match = re.search(pattern, content, re.DOTALL)
        if yaml_match:
            print(yaml_match.group(0)[:200] + "..." if len(yaml_match.group(0)) > 200 else yaml_match.group(0))
        print("\n--- 新YAML块 ---")
        print(yaml_block[:200] + "..." if len(yaml_block) > 200 else yaml_block)

    # 写入文件
    mdc_path.write_text(new_content, encoding="utf-8")


def merge_command_files(verbose=False, force=False):
    """
    将命令配置文件合并到规则目录中

    Args:
        verbose: 是否显示详细信息
        force: 是否强制重写规则文件

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
        if force:
            print("强制重写模式已启用")

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
    yaml_files = list(base_dir.glob("*_commands.yaml"))
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
                    result["failed"].append({"path": str(yaml_file), "error": "没有有效的命令配置"})
                    continue

                filtered_data, descriptions = filter_command_data(data)
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

                command_groups[group_name]["commands"].update(filtered_data["commands"])
                description_groups[group_name]["commands"].update(descriptions["commands"])

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

            # 转换为带注释的YAML格式
            yaml_content = format_yaml_with_comments(commands, description_groups[group_name], verbose)

            update_mdc_file(mdc_path, yaml_content, verbose, force)

            if verbose:
                print(f"已更新规则文件: {mdc_path}")
        except Exception as e:
            if verbose:
                print(f"更新规则文件 {mdc_path} 时出错: {str(e)}")
            result["failed"].append({"path": str(mdc_path), "error": str(e)})

    return result


if __name__ == "__main__":
    result = merge_command_files(verbose=True)
    print(f"处理完成: 成功 {len(result['success'])} 个文件, 失败 {len(result['failed'])} 个文件")
