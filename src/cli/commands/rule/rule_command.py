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
            rule list --type=core      列出特定类型的规则
            rule show <rule_id>        显示规则详情
            rule create <template_type> <name>  创建新规则
            rule edit <rule_id>        编辑规则
            rule delete <rule_id>      删除规则
            rule validate <rule_id>    验证规则
            rule export <rule_id>      导出规则
            rule import <rule_file>    导入规则

        参数:
            <rule_action>              规则操作(list/show/create/edit/delete/validate/export/import)
            <rule_id>                  规则ID
            <template_type>            模板类型
            <name>                     规则名称
            <rule_file>                规则文件路径

        选项:
            --type <type>              规则类型
            --template-dir <dir>       模板目录
            --output-dir <dir>         输出目录
            --vars <json>              变量值（JSON格式）
            --interactive              使用交互模式
            --all                      处理所有规则
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

        # 根据不同操作处理参数
        if rule_action == "list":
            # 处理list参数
            self._parse_list_args(args, parsed)
        elif rule_action == "show":
            # 处理show参数
            if args:
                parsed["rule_id"] = args.pop(0)
        elif rule_action == "create":
            # 处理create参数
            if len(args) >= 2:
                parsed["template_type"] = args.pop(0)
                parsed["name"] = args.pop(0)
            # 处理选项
            self._parse_create_options(args, parsed)
        elif rule_action == "edit":
            # 处理edit参数
            if args:
                parsed["rule_id"] = args.pop(0)
        elif rule_action == "delete":
            # 处理delete参数
            if args:
                parsed["rule_id"] = args.pop(0)
        elif rule_action == "validate":
            # 处理validate参数
            if args and not args[0].startswith("--"):
                parsed["rule_id"] = args.pop(0)
            # 检查--all选项
            if "--all" in args:
                parsed["all"] = True
                args.remove("--all")
        elif rule_action == "export":
            # 处理export参数
            if args:
                parsed["rule_id"] = args.pop(0)
                if args:
                    parsed["output_path"] = args.pop(0)
        elif rule_action == "import":
            # 处理import参数
            if args:
                parsed["rule_file"] = args.pop(0)

        return parsed

    def _parse_list_args(self, args: List[str], parsed: Dict) -> None:
        """解析list命令的参数"""
        # 处理--type选项
        i = 0
        while i < len(args):
            if args[i] == "--type" and i + 1 < len(args):
                parsed["type"] = args[i + 1]
                i += 2
            elif args[i].startswith("--type="):
                parsed["type"] = args[i].split("=", 1)[1]
                i += 1
            else:
                i += 1

    def _parse_create_options(self, args: List[str], parsed: Dict) -> None:
        """解析create命令的选项"""
        i = 0
        while i < len(args):
            if args[i] == "--template-dir" and i + 1 < len(args):
                parsed["template_dir"] = args[i + 1]
                i += 2
            elif args[i].startswith("--template-dir="):
                parsed["template_dir"] = args[i].split("=", 1)[1]
                i += 1
            elif args[i] == "--output-dir" and i + 1 < len(args):
                parsed["output_dir"] = args[i + 1]
                i += 2
            elif args[i].startswith("--output-dir="):
                parsed["output_dir"] = args[i].split("=", 1)[1]
                i += 1
            elif args[i] == "--vars" and i + 1 < len(args):
                parsed["vars"] = args[i + 1]
                i += 2
            elif args[i].startswith("--vars="):
                parsed["vars"] = args[i].split("=", 1)[1]
                i += 1
            elif args[i] == "--interactive":
                parsed["interactive"] = True
                i += 1
            else:
                i += 1

    def execute(self, parsed_args: Dict) -> None:
        """执行命令 - 适配新接口"""
        # 处理字典参数
        if isinstance(parsed_args, dict):
            rule_action = parsed_args.get("rule_action")
            show_help_flag = parsed_args.get("show_help", False)
        else:
            return  # 不支持非字典参数

        # 处理帮助
        if show_help_flag:
            help_result = show_help()
            if isinstance(help_result, dict) and "message" in help_result:
                print(help_result["message"])
            return
        # 如果没有指定操作，默认为list
        elif rule_action is None:
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
        elif rule_action == "edit":
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

                # 处理数据
                if "data" in result:
                    data = result["data"]
                    if isinstance(data, list):
                        # 列表结果
                        for item in data:
                            if isinstance(item, dict) and "id" in item and "name" in item:
                                print(f"{item['id']}: {item['name']}")
                            else:
                                print(item)
                    elif isinstance(data, dict):
                        # 字典结果
                        if "content" in data:
                            print(data["content"])
                        else:
                            for k, v in data.items():
                                print(f"{k}: {v}")
                    else:
                        # 其他类型
                        print(data)
            else:
                # 输出错误信息
                print(f"错误: {result.get('error', '未知错误')}")

    def _execute_impl(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行规则命令（兼容旧接口）"""
        # 从args中获取操作类型
        rule_action = args.get("rule_action")

        # 处理帮助
        if rule_action == "help" or args.get("help", False):
            return show_help()

        # 根据操作类型执行相应的处理函数
        if rule_action == "create":
            return convert_result(create_rule(self.template_manager, self.rule_generator, args))
        elif rule_action == "list":
            return convert_result(list_rules(self.template_manager, args))
        elif rule_action == "show":
            return convert_result(show_rule(self.template_manager, args))
        elif rule_action == "edit":
            return convert_result(edit_rule(self.template_manager, args))
        elif rule_action == "delete":
            return convert_result(delete_rule(self.template_manager, args))
        elif rule_action == "validate":
            return convert_result(validate_rule(self.template_manager, args))
        elif rule_action == "export":
            return convert_result(export_rule(self.template_manager, args))
        elif rule_action == "import":
            return convert_result(import_rule(self.template_manager, args))
        else:
            logger.error("未知的规则操作: %s", rule_action)
            return {"success": False, "error": f"未知的规则操作: {rule_action}"}
