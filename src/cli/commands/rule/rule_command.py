"""
规则管理命令模块

处理规则相关的命令，包括创建、查看、修改、删除规则等操作。
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.cli.base_command import BaseCommand
from src.cli.command import Command
from src.cli.commands.rule.rule_command_handlers import (
    create_rule,
    delete_rule,
    edit_rule,
    export_rule,
    import_rule,
    list_rules,
    show_rule,
    validate_rule,
)
from src.cli.commands.rule.rule_command_utils import convert_result, show_help
from src.templates.core.rule_generator import RuleGenerator
from src.templates.core.template_engine import TemplateEngine
from src.templates.core.template_manager import TemplateManager
from src.workflow.workflow_utils import get_session

logger = logging.getLogger(__name__)


class RuleCommand(BaseCommand, Command):
    """规则管理命令处理器"""

    def __init__(self):
        super().__init__("rule", "规则管理命令")
        self.template_engine = TemplateEngine()
        # 获取数据库会话并使用它初始化TemplateManager
        self.session = get_session()
        self.template_manager = TemplateManager(session=self.session)
        self.rule_generator = RuleGenerator(template_engine=self.template_engine)

    # 实现新接口
    @classmethod
    def get_command(cls) -> str:
        return "rule"

    @classmethod
    def get_description(cls) -> str:
        return "规则管理命令"

    @classmethod
    def get_help(cls) -> str:
        return """
规则管理命令

用法:
    rule list                  列出所有规则
    rule list [--type=<rule_type>] [--verbose]     列出特定类型的规则
    rule show <id> [--format=<json|text>]         显示规则详情
    rule create <template_type> <name> [--vars=<json>]  创建新规则
    rule update <id> [--vars=<json>]       更新规则
    rule delete <id> [--force]          删除规则
    rule validate <id> [--all]         验证规则
    rule export <id> [--output=<path>] [--format=<format>]  导出规则
    rule import <file_path> [--overwrite]       导入规则

参数:
    <id>                  规则ID
    <template_type>       模板类型
    <name>                规则名称
    <file_path>           规则文件路径

选项:
    --type=<rule_type>    规则类型
    --format=<format>     输出格式 (json或text)
    --vars=<json>         变量值（JSON格式）
    --output=<path>       输出路径
    --force               强制执行危险操作
    --verbose             显示详细信息
    --all                 处理所有规则
    --overwrite           覆盖已存在的规则
"""

    def parse_args(self, args: List[str]) -> Dict:
        """解析命令参数"""
        parsed = {"command": self.get_command()}

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
            self._parse_list_args(args, parsed)
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
            self._parse_create_options(args, parsed)
        elif rule_action == "update":
            # 处理update参数
            if args:
                parsed["id"] = args.pop(0)
            # 处理选项
            self._parse_create_options(args, parsed)
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

    def _parse_list_args(self, args: List[str], parsed: Dict) -> None:
        """解析list命令的参数"""
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

    def _parse_create_options(self, args: List[str], parsed: Dict) -> None:
        """解析create/update命令的选项"""
        for i, arg in enumerate(args):
            if arg == "--vars" and i + 1 < len(args):
                parsed["vars"] = args[i + 1]
                args[i : i + 2] = []
                break
            elif arg.startswith("--vars="):
                parsed["vars"] = arg.split("=", 1)[1]
                args.remove(arg)
                break

    def execute(self, args) -> None:
        """执行命令 - 适配新接口"""
        # 处理参数
        parsed_args = {}
        if isinstance(args, list):
            # 如果是列表参数，首先解析成字典
            if not args or "--help" in args or "-h" in args:
                print(self.get_help())
                return
            parsed_args = self.parse_args(args)
        elif isinstance(args, dict):
            # 如果已经是字典，直接使用
            parsed_args = args
            # 处理帮助标识
            if not parsed_args or parsed_args.get("show_help", False):
                print(self.get_help())
                return
        else:
            # 不支持其他类型参数
            print("错误: 不支持的参数类型")
            return

        # 处理字典参数
        rule_action = parsed_args.get("rule_action")

        # 如果没有指定操作，默认为list
        if rule_action is None:
            result = list_rules(self.template_manager, parsed_args)
            result = convert_result(result)
        # 处理具体操作
        elif rule_action == "create":
            result = create_rule(self.template_manager, self.rule_generator, parsed_args)
            result = convert_result(result)
        elif rule_action == "list":
            result = list_rules(self.template_manager, parsed_args)
            result = convert_result(result)
        elif rule_action == "show":
            result = show_rule(self.template_manager, parsed_args)
            result = convert_result(result)
        elif rule_action == "update":
            result = edit_rule(self.template_manager, parsed_args)
            result = convert_result(result)
        elif rule_action == "delete":
            result = delete_rule(self.template_manager, parsed_args)
            result = convert_result(result)
        elif rule_action == "validate":
            result = validate_rule(self.template_manager, parsed_args)
            result = convert_result(result)
        elif rule_action == "export":
            result = export_rule(self.template_manager, parsed_args)
            result = convert_result(result)
        elif rule_action == "import":
            result = import_rule(self.template_manager, parsed_args)
            result = convert_result(result)
        else:
            logger.error("未知的规则操作: %s", rule_action)
            result = {"success": False, "error": f"未知的规则操作: {rule_action}"}

        # 格式化输出
        if isinstance(result, dict):
            if result.get("success", False):
                # 输出结果
                if "message" in result:
                    print(result["message"])
                elif "data" in result:
                    # 格式化输出
                    output_format = parsed_args.get("format", "text")
                    if output_format == "json":
                        print(json.dumps(result["data"], ensure_ascii=False, indent=2))
                    else:
                        if isinstance(result["data"], dict):
                            for k, v in result["data"].items():
                                print(f"{k}: {v}")
                        elif isinstance(result["data"], list):
                            for item in result["data"]:
                                print(item)
                        else:
                            print(result["data"])
            else:
                # 输出错误
                if "error" in result:
                    print(f"错误: {result['error']}")
                else:
                    print("执行失败")

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """实现BaseCommand接口的执行方法"""
        # 解析参数
        rule_action = args.get("rule_action")

        # 根据操作调用对应处理函数
        if rule_action == "list":
            result = list_rules(self.template_manager, args)
        elif rule_action == "show":
            result = show_rule(self.template_manager, args)
        elif rule_action == "create":
            result = create_rule(self.template_manager, self.rule_generator, args)
        elif rule_action == "update":
            result = edit_rule(self.template_manager, args)
        elif rule_action == "delete":
            result = delete_rule(self.template_manager, args)
        elif rule_action == "validate":
            result = validate_rule(self.template_manager, args)
        elif rule_action == "export":
            result = export_rule(self.template_manager, args)
        elif rule_action == "import":
            result = import_rule(self.template_manager, args)
        else:
            return {"success": False, "error": f"未知的规则操作: {rule_action}"}

        return convert_result(result)
