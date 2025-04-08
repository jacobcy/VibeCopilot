"""
规则命令参数解析模块

提供解析规则命令参数的功能。
"""

import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def parse_rule_args(args: List[str]) -> Dict:
    """
    解析规则命令的参数

    Args:
        args: 命令行参数列表

    Returns:
        解析后的参数字典
    """
    parsed = {"command": "rule"}

    # 处理帮助选项
    if not args or "--help" in args or "-h" in args:
        parsed["show_help"] = True
        return parsed

    # 处理规则操作
    rule_action = args.pop(0)
    parsed["rule_action"] = rule_action

    # 通用选项
    parsed["verbose"] = "--verbose" in args
    if "--verbose" in args:
        args.remove("--verbose")

    # 处理格式选项
    for i, arg in enumerate(args):
        if arg == "--format" and i + 1 < len(args):
            parsed["format"] = args[i + 1]
            args[i : i + 2] = []
            break
        elif arg.startswith("--format="):
            parsed["format"] = arg.split("=", 1)[1]
            args.remove(arg)
            break

    # 根据不同操作处理参数
    if rule_action == "list":
        # 处理list参数
        _parse_list_args(args, parsed)
    elif rule_action == "show":
        # 处理show参数
        if args:
            parsed["id"] = args.pop(0)
    elif rule_action == "create":
        # 处理create参数
        if len(args) >= 2:
            parsed["template_type"] = args.pop(0)
            parsed["name"] = args.pop(0)
        # 处理选项
        _parse_create_options(args, parsed)
    elif rule_action == "update":
        # 处理update参数
        if args:
            parsed["id"] = args.pop(0)
        # 处理选项
        _parse_create_options(args, parsed)
    elif rule_action == "delete":
        # 处理delete参数
        if args:
            parsed["id"] = args.pop(0)
        parsed["force"] = "--force" in args
        if "--force" in args:
            args.remove("--force")
    elif rule_action == "validate":
        # 处理validate参数
        if args and not args[0].startswith("--"):
            parsed["id"] = args.pop(0)
        # 检查--all选项
        parsed["all"] = "--all" in args
        if "--all" in args:
            args.remove("--all")
    elif rule_action == "export":
        # 处理export参数
        if args and not args[0].startswith("--"):
            parsed["id"] = args.pop(0)

        # 处理--output选项
        for i, arg in enumerate(args):
            if arg == "--output" and i + 1 < len(args):
                parsed["output"] = args[i + 1]
                args[i : i + 2] = []
                break
            elif arg.startswith("--output="):
                parsed["output"] = arg.split("=", 1)[1]
                args.remove(arg)
                break
    elif rule_action == "import":
        # 处理import参数
        if args and not args[0].startswith("--"):
            parsed["file_path"] = args.pop(0)
        parsed["overwrite"] = "--overwrite" in args
        if "--overwrite" in args:
            args.remove("--overwrite")

    return parsed


def _parse_list_args(args: List[str], parsed: Dict) -> None:
    """
    解析list命令的参数

    Args:
        args: 命令行参数列表
        parsed: 解析结果字典
    """
    # 处理--type选项
    for i, arg in enumerate(args):
        if arg == "--type" and i + 1 < len(args):
            parsed["type"] = args[i + 1]
            args[i : i + 2] = []
            break
        elif arg.startswith("--type="):
            parsed["type"] = arg.split("=", 1)[1]
            args.remove(arg)
            break


def _parse_create_options(args: List[str], parsed: Dict) -> None:
    """
    解析create/update命令的选项

    Args:
        args: 命令行参数列表
        parsed: 解析结果字典
    """
    # 处理 --vars 选项
    for i, arg in enumerate(args):
        if arg == "--vars" and i + 1 < len(args):
            try:
                # 尝试解析JSON字符串
                vars_str = args[i + 1]
                if vars_str.startswith("'") and vars_str.endswith("'"):
                    vars_str = vars_str[1:-1]
                vars_json = json.loads(vars_str)
                parsed["vars"] = vars_json
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {str(e)}")
                parsed["vars"] = args[i + 1]  # 保存原始字符串
            args[i : i + 2] = []
            break
        elif arg.startswith("--vars="):
            vars_str = arg.split("=", 1)[1]
            # 去掉可能的引号
            if vars_str.startswith("'") and vars_str.endswith("'"):
                vars_str = vars_str[1:-1]
            if vars_str.startswith('"') and vars_str.endswith('"'):
                vars_str = vars_str[1:-1]

            try:
                # 尝试解析JSON字符串
                vars_json = json.loads(vars_str)
                parsed["vars"] = vars_json
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {str(e)}")
                parsed["vars"] = vars_str  # 保存原始字符串
            args.remove(arg)
            break
