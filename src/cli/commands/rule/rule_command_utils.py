"""
规则命令辅助工具
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from src.models.db import Template

logger = logging.getLogger(__name__)


def get_template(template_manager, template_type: str) -> Optional[Template]:
    """获取指定类型的模板"""
    try:
        templates = template_manager.get_templates_by_type(template_type)
        if not templates:
            logger.error("未找到模板类型: %s", template_type)
            return None
        return templates[0]
    except Exception as e:
        logger.error("获取模板失败: %s", str(e))
        return None


def prepare_variables(args) -> Optional[Dict]:
    """准备模板变量"""
    try:
        # 获取参数
        if isinstance(args, dict):
            name = args.get("name")
            vars_json = args.get("vars")
        else:
            name = args.name
            vars_json = getattr(args, "vars", None)

        # 初始化变量
        variables = {"name": name}

        # 解析JSON变量
        if vars_json:
            try:
                additional_vars = json.loads(vars_json)
                variables.update(additional_vars)
            except json.JSONDecodeError:
                logger.error("无效的JSON变量格式")
                return None

        return variables

    except Exception as e:
        logger.error("准备变量失败: %s", str(e))
        return None


def convert_result(result) -> Dict[str, Any]:
    """转换整数结果为字典结果"""
    if isinstance(result, int):
        if result == 0:
            return {"success": True, "message": "操作成功完成"}
        else:
            return {"success": False, "error": "操作失败"}
    return result


def validate_single_rule(rule) -> bool:
    """验证单个规则"""
    try:
        # TODO: 实现规则验证逻辑
        logger.info("验证规则: %s", rule.id)
        return True
    except Exception as e:
        logger.error("验证规则失败: %s: %s", rule.id, str(e))
        return False


def show_help() -> Dict[str, Any]:
    """显示命令帮助"""
    help_text = """
规则管理命令 (rule)

用法:
  rule list [--type=<rule_type>] [--verbose]
  rule show <id> [--format=<json|text>]
  rule create <template_type> <n> [--vars=<json>]
  rule update <id> [--vars=<json>]
  rule delete <id> [--force]
  rule enable <id>
  rule disable <id>
  rule edit <id>

参数说明:
  template_type: 规则模板类型，可选值：
    - agent: 代理规则
    - auto: 自动化规则
    - best_practices: 最佳实践规则
    - command: 命令规则
    - role: 角色规则
    - workflow: 工作流规则

示例:
  rule create command my-rule --vars='{"description":"这是一个命令规则"}'
  rule list --type=command
  rule show my-rule
  rule delete my-rule --force
  rule enable my-rule
  rule disable my-rule
  rule edit my-rule
"""
    return {"success": True, "message": help_text}
