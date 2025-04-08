"""
路线图命令参数解析模块

提供解析路线图命令参数的功能。
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def parse_roadmap_args(args: List[str]) -> Dict:
    """
    解析路线图命令的参数

    Args:
        args: 命令行参数列表

    Returns:
        解析后的参数字典
    """
    parsed = {"command": "roadmap"}

    # 处理帮助选项
    if not args or "--help" in args or "-h" in args:
        parsed["show_help"] = True
        return parsed

    # 处理路线图操作
    roadmap_action = args.pop(0)
    parsed["roadmap_action"] = roadmap_action

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
    if roadmap_action == "list":
        # 不需要额外处理
        pass
    elif roadmap_action == "show":
        # 处理show参数
        if args:
            parsed["id"] = args.pop(0)
    elif roadmap_action == "create":
        # 处理create参数
        for i, arg in enumerate(args):
            if arg.startswith("--name="):
                parsed["name"] = arg.split("=", 1)[1]
                args.remove(arg)
                break
            elif arg == "--name" and i + 1 < len(args):
                parsed["name"] = args[i + 1]
                args[i : i + 2] = []
                break

        for i, arg in enumerate(args):
            if arg.startswith("--desc="):
                parsed["description"] = arg.split("=", 1)[1]
                args.remove(arg)
                break
            elif arg == "--desc" and i + 1 < len(args):
                parsed["description"] = args[i + 1]
                args[i : i + 2] = []
                break
    elif roadmap_action == "update":
        # 处理update参数
        if args and not args[0].startswith("--"):
            parsed["id"] = args.pop(0)

        # 解析name和description参数
        for i, arg in enumerate(args):
            if arg.startswith("--name="):
                parsed["name"] = arg.split("=", 1)[1]
                args.remove(arg)
                break
            elif arg == "--name" and i + 1 < len(args):
                parsed["name"] = args[i + 1]
                args[i : i + 2] = []
                break

        for i, arg in enumerate(args):
            if arg.startswith("--desc="):
                parsed["description"] = arg.split("=", 1)[1]
                args.remove(arg)
                break
            elif arg == "--desc" and i + 1 < len(args):
                parsed["description"] = args[i + 1]
                args[i : i + 2] = []
                break
    elif roadmap_action == "delete":
        # 处理delete参数
        if args and not args[0].startswith("--"):
            parsed["id"] = args.pop(0)
        parsed["force"] = "--force" in args
        if "--force" in args:
            args.remove("--force")
    elif roadmap_action == "sync":
        # 处理sync参数
        for i, arg in enumerate(args):
            if arg.startswith("--source="):
                parsed["source"] = arg.split("=", 1)[1]
                args.remove(arg)
                break
            elif arg == "--source" and i + 1 < len(args):
                parsed["source"] = args[i + 1]
                args[i : i + 2] = []
                break
    elif roadmap_action == "switch":
        # 处理switch参数
        if args:
            parsed["id"] = args.pop(0)
    elif roadmap_action == "status":
        # 处理status参数
        if args:
            parsed["id"] = args.pop(0)

    return parsed
