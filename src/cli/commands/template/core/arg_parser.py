"""
模板命令参数解析模块

提供解析模板命令参数的功能。
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def parse_template_args(args: List[str]) -> Dict:
    """
    解析模板命令的参数

    Args:
        args: 命令行参数列表

    Returns:
        解析后的参数字典
    """
    parsed = {"command": "template"}

    # 处理帮助选项
    if not args or "--help" in args or "-h" in args:
        parsed["show_help"] = True
        return parsed

    # 处理模板操作
    template_action = args.pop(0)
    parsed["template_action"] = template_action

    # 根据不同操作处理参数
    if template_action == "list":
        _parse_list_args(args, parsed)
    elif template_action == "show":
        _parse_show_args(args, parsed)
    elif template_action == "import":
        _parse_import_args(args, parsed)
    elif template_action == "create":
        _parse_create_args(args, parsed)
    elif template_action == "update":
        _parse_update_args(args, parsed)
    elif template_action == "delete":
        _parse_delete_args(args, parsed)
    elif template_action == "generate":
        _parse_generate_args(args, parsed)
    elif template_action == "load":
        _parse_load_args(args, parsed)
    elif template_action == "export":
        _parse_export_args(args, parsed)
    elif template_action == "init":
        _parse_init_args(args, parsed)

    return parsed


def _parse_list_args(args: List[str], parsed: Dict) -> None:
    """解析list命令的参数"""
    # 处理type参数
    for i, arg in enumerate(args):
        if arg.startswith("--type="):
            parsed["template_type"] = arg.split("=", 1)[1]
            args.remove(arg)
            break
        elif arg == "--type" and i + 1 < len(args):
            parsed["template_type"] = args[i + 1]
            args[i : i + 2] = []
            break

    # 处理verbose参数
    if "--verbose" in args:
        parsed["verbose"] = True
        args.remove("--verbose")


def _parse_show_args(args: List[str], parsed: Dict) -> None:
    """解析show命令的参数"""
    # 处理ID参数
    if args:
        parsed["id"] = args.pop(0)

    # 处理format参数
    for i, arg in enumerate(args):
        if arg.startswith("--format="):
            parsed["format"] = arg.split("=", 1)[1]
            args.remove(arg)
            break
        elif arg == "--format" and i + 1 < len(args):
            parsed["format"] = args[i + 1]
            args[i : i + 2] = []
            break


def _parse_import_args(args: List[str], parsed: Dict) -> None:
    """解析import命令的参数"""
    # 处理file_path参数
    if args:
        parsed["file_path"] = args.pop(0)

    # 处理overwrite参数
    if "--overwrite" in args:
        parsed["overwrite"] = True
        args.remove("--overwrite")

    # 处理recursive参数
    if "--recursive" in args:
        parsed["recursive"] = True
        args.remove("--recursive")


def _parse_create_args(args: List[str], parsed: Dict) -> None:
    """解析create命令的参数"""
    # 处理name参数
    for i, arg in enumerate(args):
        if arg.startswith("--name="):
            parsed["name"] = arg.split("=", 1)[1]
            args.remove(arg)
            break
        elif arg == "--name" and i + 1 < len(args):
            parsed["name"] = args[i + 1]
            args[i : i + 2] = []
            break

    # 处理type参数
    for i, arg in enumerate(args):
        if arg.startswith("--type="):
            parsed["template_type"] = arg.split("=", 1)[1]
            args.remove(arg)
            break
        elif arg == "--type" and i + 1 < len(args):
            parsed["template_type"] = args[i + 1]
            args[i : i + 2] = []
            break

    # 处理description参数
    for i, arg in enumerate(args):
        if arg.startswith("--description="):
            parsed["description"] = arg.split("=", 1)[1]
            args.remove(arg)
            break
        elif arg == "--description" and i + 1 < len(args):
            parsed["description"] = args[i + 1]
            args[i : i + 2] = []
            break


def _parse_update_args(args: List[str], parsed: Dict) -> None:
    """解析update命令的参数"""
    # 处理ID参数
    if args:
        parsed["id"] = args.pop(0)

    # 处理name参数
    for i, arg in enumerate(args):
        if arg.startswith("--name="):
            parsed["name"] = arg.split("=", 1)[1]
            args.remove(arg)
            break
        elif arg == "--name" and i + 1 < len(args):
            parsed["name"] = args[i + 1]
            args[i : i + 2] = []
            break


def _parse_delete_args(args: List[str], parsed: Dict) -> None:
    """解析delete命令的参数"""
    # 处理ID参数
    if args:
        parsed["id"] = args.pop(0)

    # 处理force参数
    if "--force" in args:
        parsed["force"] = True
        args.remove("--force")


def _parse_generate_args(args: List[str], parsed: Dict) -> None:
    """解析generate命令的参数"""
    # 处理ID参数
    if args:
        parsed["id"] = args.pop(0)

    # 处理output参数
    if args:
        parsed["output"] = args.pop(0)

    # 处理变量参数
    for i, arg in enumerate(args):
        if arg.startswith("--vars="):
            parsed["variables"] = arg.split("=", 1)[1]
            args.remove(arg)
            break
        elif arg == "--vars" and i + 1 < len(args):
            parsed["variables"] = args[i + 1]
            args[i : i + 2] = []
            break


def _parse_load_args(args: List[str], parsed: Dict) -> None:
    """解析load命令的参数"""
    # 处理目录参数
    for i, arg in enumerate(args):
        if arg.startswith("--dir="):
            parsed["templates_dir"] = arg.split("=", 1)[1]
            args.remove(arg)
            break
        elif arg == "--dir" and i + 1 < len(args):
            parsed["templates_dir"] = args[i + 1]
            args[i : i + 2] = []
            break


def _parse_export_args(args: List[str], parsed: Dict) -> None:
    """解析export命令的参数"""
    # 处理ID参数
    if args:
        parsed["id"] = args.pop(0)

    # 处理output参数
    for i, arg in enumerate(args):
        if arg.startswith("--output="):
            parsed["output"] = arg.split("=", 1)[1]
            args.remove(arg)
            break
        elif arg == "--output" and i + 1 < len(args):
            parsed["output"] = args[i + 1]
            args[i : i + 2] = []
            break

    # 处理format参数
    for i, arg in enumerate(args):
        if arg.startswith("--format="):
            parsed["format"] = arg.split("=", 1)[1]
            args.remove(arg)
            break
        elif arg == "--format" and i + 1 < len(args):
            parsed["format"] = args[i + 1]
            args[i : i + 2] = []
            break


def _parse_init_args(args: List[str], parsed: Dict) -> None:
    """解析init命令的参数"""
    # 处理force参数
    if "--force" in args:
        parsed["force"] = True
        args.remove("--force")

    # 处理source参数
    for i, arg in enumerate(args):
        if arg.startswith("--source="):
            parsed["source"] = arg.split("=", 1)[1]
            args.remove(arg)
            break
        elif arg == "--source" and i + 1 < len(args):
            parsed["source"] = args[i + 1]
            args[i : i + 2] = []
            break
