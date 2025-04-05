"""
规则管理命令处理器
"""

import logging
from typing import Any, Dict

from src.cli.base_command import BaseCommand
from src.cli.commands.rule_command_handlers import (
    create_rule,
    delete_rule,
    edit_rule,
    export_rule,
    import_rule,
    list_rules,
    show_rule,
    validate_rule,
)
from src.cli.commands.rule_command_utils import convert_result, show_help
from src.templates.core.rule_generator import RuleGenerator
from src.templates.core.template_engine import TemplateEngine
from src.templates.core.template_manager import TemplateManager

logger = logging.getLogger(__name__)


class RuleCommand(BaseCommand):
    """规则管理命令处理器"""

    def __init__(self):
        super().__init__("rule", "规则管理命令")
        self.template_engine = TemplateEngine()
        self.template_manager = TemplateManager()
        self.rule_generator = RuleGenerator(template_engine=self.template_engine)

    def setup_arguments(self, parser):
        """设置命令参数"""
        subparsers = parser.add_subparsers(dest="rule_action", help="规则操作")

        # create 命令
        create_parser = subparsers.add_parser("create", help="创建新规则")
        create_parser.add_argument("template_type", help="模板类型")
        create_parser.add_argument("name", help="规则名称")
        create_parser.add_argument("--template-dir", help="模板目录")
        create_parser.add_argument("--output-dir", help="输出目录")
        create_parser.add_argument("--vars", help="变量值（JSON格式）")
        create_parser.add_argument("--interactive", action="store_true", help="使用交互模式")

        # list 命令
        list_parser = subparsers.add_parser("list", help="列出规则")
        list_parser.add_argument("--type", help="规则类型")

        # show 命令
        show_parser = subparsers.add_parser("show", help="显示规则详情")
        show_parser.add_argument("rule_id", help="规则ID")

        # edit 命令
        edit_parser = subparsers.add_parser("edit", help="编辑规则")
        edit_parser.add_argument("rule_id", help="规则ID")

        # delete 命令
        delete_parser = subparsers.add_parser("delete", help="删除规则")
        delete_parser.add_argument("rule_id", help="规则ID")

        # validate 命令
        validate_parser = subparsers.add_parser("validate", help="验证规则")
        validate_parser.add_argument("rule_id", help="规则ID")
        validate_parser.add_argument("--all", action="store_true", help="验证所有规则")

        # export 命令
        export_parser = subparsers.add_parser("export", help="导出规则")
        export_parser.add_argument("rule_id", help="规则ID")
        export_parser.add_argument("output_path", nargs="?", help="输出路径")

        # import 命令
        import_parser = subparsers.add_parser("import", help="导入规则")
        import_parser.add_argument("rule_file", help="规则文件路径")

    def execute(self, args) -> Dict[str, Any]:
        """执行命令"""
        # 处理字典参数
        if isinstance(args, dict):
            rule_action = args.get("rule_action")
            show_help_flag = args.get("help", False)
        else:
            rule_action = getattr(args, "rule_action", None)
            show_help_flag = getattr(args, "help", False)

        # 处理帮助
        if show_help_flag:
            return show_help()

        # 如果没有指定操作，默认为list
        if rule_action is None:
            result = list_rules(self.template_manager, args)
            return convert_result(result)

        # 处理具体操作
        if rule_action == "create":
            result = create_rule(self.template_manager, self.rule_generator, args)
        elif rule_action == "list":
            result = list_rules(self.template_manager, args)
        elif rule_action == "show":
            result = show_rule(self.template_manager, args)
        elif rule_action == "edit":
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
            logger.error("未知的规则操作: %s", rule_action)
            return {"success": False, "error": f"未知的规则操作: {rule_action}"}

        return convert_result(result)
