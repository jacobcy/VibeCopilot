"""
规则列表和查看相关处理函数

提供规则列表和详情查看相关功能实现。
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def list_rules(template_manager, args) -> Dict[str, Any]:
    """列出规则

    Args:
        template_manager: 模板管理器
        args: 命令参数

    Returns:
        处理结果
    """
    try:
        rules = template_manager.get_all_templates()
        rule_type = args.get("type") if isinstance(args, dict) else getattr(args, "type", None)
        verbose = (
            args.get("verbose", False)
            if isinstance(args, dict)
            else getattr(args, "verbose", False)
        )

        if rule_type:
            rules = [r for r in rules if r.type == rule_type]

        if not rules:
            return {"success": True, "message": "没有找到规则", "data": []}

        result_data = []
        for rule in rules:
            if verbose:
                result_data.append(
                    {
                        "id": rule.id,
                        "name": rule.name,
                        "type": rule.type,
                        "description": rule.description,
                    }
                )
            else:
                result_data.append(f"{rule.id}: {rule.name} ({rule.type})")

        return {"success": True, "data": result_data}

    except Exception as e:
        logger.error("列出规则失败: %s", str(e))
        return {"success": False, "error": f"列出规则失败: {str(e)}"}


def show_rule(template_manager, args) -> Dict[str, Any]:
    """显示规则详情

    Args:
        template_manager: 模板管理器
        args: 命令参数

    Returns:
        处理结果
    """
    try:
        rule_id = args.get("id") if isinstance(args, dict) else args.id
        format_type = (
            args.get("format", "text")
            if isinstance(args, dict)
            else getattr(args, "format", "text")
        )

        rule = template_manager.get_template(rule_id)
        if not rule:
            logger.error("未找到规则: %s", rule_id)
            return {"success": False, "error": f"未找到规则: {rule_id}"}

        if format_type == "json":
            return {
                "success": True,
                "data": {
                    "id": rule.id,
                    "name": rule.name,
                    "type": rule.type,
                    "description": rule.description,
                    "content": rule.content,
                },
            }
        else:
            result = {
                "success": True,
                "data": {
                    "ID": rule.id,
                    "名称": rule.name,
                    "类型": rule.type,
                    "描述": rule.description,
                    "内容": rule.content,
                },
            }
            return result

    except Exception as e:
        logger.error("显示规则失败: %s", str(e))
        return {"success": False, "error": f"显示规则失败: {str(e)}"}
