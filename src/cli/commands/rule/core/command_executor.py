"""
规则命令执行模块

提供执行规则命令的具体逻辑。
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

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
from src.cli.commands.rule.rule_command_utils import convert_result
from src.templates.core.rule_generator import RuleGenerator
from src.templates.core.template_engine import TemplateEngine
from src.templates.core.template_manager import TemplateManager

logger = logging.getLogger(__name__)


class RuleCommandExecutor:
    """规则命令执行器"""

    def __init__(
        self,
        session: Optional[Session] = None,
        template_engine: Optional[TemplateEngine] = None,
        template_manager: Optional[TemplateManager] = None,
        rule_generator: Optional[RuleGenerator] = None,
    ):
        """
        初始化规则命令执行器

        Args:
            session: 数据库会话
            template_engine: 模板引擎
            template_manager: 模板管理器
            rule_generator: 规则生成器
        """
        self.session = session
        self.template_engine = template_engine or TemplateEngine()
        self.template_manager = template_manager
        self.rule_generator = rule_generator or (RuleGenerator(template_engine=self.template_engine) if not rule_generator else rule_generator)

    def execute_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行规则命令

        Args:
            args: 命令参数字典

        Returns:
            执行结果
        """
        # 获取操作类型
        rule_action = args.get("rule_action")

        # 根据操作类型执行相应命令
        if rule_action == "list":
            return self._execute_list(args)
        elif rule_action == "show":
            return self._execute_show(args)
        elif rule_action == "create":
            return self._execute_create(args)
        elif rule_action == "update":
            return self._execute_update(args)
        elif rule_action == "delete":
            return self._execute_delete(args)
        elif rule_action == "validate":
            return self._execute_validate(args)
        elif rule_action == "export":
            return self._execute_export(args)
        elif rule_action == "import":
            return self._execute_import(args)
        else:
            logger.error(f"未知的规则操作: {rule_action}")
            return {"success": False, "error": f"未知的规则操作: {rule_action}"}

    def _execute_list(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行list命令"""
        rule_type = args.get("type")
        verbose = args.get("verbose", False)
        return list_rules(self.session, rule_type, verbose)

    def _execute_show(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行show命令"""
        rule_id = args.get("id")
        format_type = args.get("format", "text")
        if not rule_id:
            return {"success": False, "error": "未提供规则ID"}
        return show_rule(self.session, rule_id, format_type)

    def _execute_create(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行create命令"""
        template_type = args.get("template_type")
        name = args.get("name")
        vars_dict = args.get("vars", {})

        if not template_type or not name:
            return {"success": False, "error": "未提供必要的参数"}

        return create_rule(self.session, template_type, name, vars_dict, template_manager=self.template_manager, rule_generator=self.rule_generator)

    def _execute_update(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行update命令"""
        rule_id = args.get("id")
        vars_dict = args.get("vars", {})

        if not rule_id:
            return {"success": False, "error": "未提供规则ID"}

        return edit_rule(self.session, rule_id, vars_dict, template_manager=self.template_manager, rule_generator=self.rule_generator)

    def _execute_delete(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行delete命令"""
        rule_id = args.get("id")
        force = args.get("force", False)

        if not rule_id:
            return {"success": False, "error": "未提供规则ID"}

        return delete_rule(self.session, rule_id, force)

    def _execute_validate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行validate命令"""
        rule_id = args.get("id")
        all_rules = args.get("all", False)

        if not rule_id and not all_rules:
            return {"success": False, "error": "未提供规则ID且未指定--all选项"}

        return validate_rule(self.session, rule_id, all_rules)

    def _execute_export(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行export命令"""
        rule_id = args.get("id")
        output_path = args.get("output")
        format_type = args.get("format", "yaml")

        if not rule_id:
            return {"success": False, "error": "未提供规则ID"}

        return export_rule(self.session, rule_id, output_path, format_type)

    def _execute_import(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行import命令"""
        file_path = args.get("file_path")
        overwrite = args.get("overwrite", False)

        if not file_path:
            return {"success": False, "error": "未提供文件路径"}

        return import_rule(self.session, file_path, overwrite)
