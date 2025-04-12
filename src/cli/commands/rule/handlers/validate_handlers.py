"""
规则验证相关处理函数

提供规则验证相关功能实现。
"""

import logging
from typing import Any, Dict, List

from src.cli.commands.rule.utils import validate_single_rule

logger = logging.getLogger(__name__)


def validate_rule(template_manager, args) -> Dict[str, Any]:
    """验证规则

    Args:
        template_manager: 模板管理器
        args: 命令参数

    Returns:
        处理结果
    """
    try:
        validate_all = args.get("all", False) if isinstance(args, dict) else getattr(args, "all", False)

        if validate_all:
            rules = template_manager.get_all_templates()
            if not rules:
                return {"success": True, "message": "没有找到规则进行验证"}

            success = True
            results = []
            for rule in rules:
                valid = validate_single_rule(rule)
                results.append({"id": rule.id, "valid": valid})
                if not valid:
                    success = False

            return {
                "success": True,
                "message": "所有规则验证完成" if success else "部分规则验证失败",
                "data": results,
            }
        else:
            rule_id = args.get("id") if isinstance(args, dict) else args.id
            rule = template_manager.get_template(rule_id)
            if not rule:
                logger.error("未找到规则: %s", rule_id)
                return {"success": False, "error": f"未找到规则: {rule_id}"}

            valid = validate_single_rule(rule)
            return {
                "success": True,
                "message": f"规则验证{'成功' if valid else '失败'}: {rule_id}",
                "data": {"id": rule_id, "valid": valid},
            }

    except Exception as e:
        logger.error("验证规则失败: %s", str(e))
        return {"success": False, "error": f"验证规则失败: {str(e)}"}
