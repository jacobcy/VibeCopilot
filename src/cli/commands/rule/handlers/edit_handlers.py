"""
规则编辑和删除相关处理函数

提供规则编辑和删除相关功能实现。
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def edit_rule(template_manager, args) -> Dict[str, Any]:
    """编辑规则

    Args:
        template_manager: 模板管理器
        args: 命令参数

    Returns:
        处理结果
    """
    try:
        rule_id = args.get("id") if isinstance(args, dict) else args.id
        rule = template_manager.get_template(rule_id)
        if not rule:
            logger.error("未找到规则: %s", rule_id)
            return {"success": False, "error": f"未找到规则: {rule_id}"}

        # 暂时还没实现完整的编辑功能，仅支持通过vars更新
        vars_json = args.get("vars") if isinstance(args, dict) else getattr(args, "vars", None)
        if vars_json:
            try:
                vars_data = json.loads(vars_json)
                # 这里添加更新规则的逻辑
                logger.info("规则更新功能尚未完全实现")
                return {"success": True, "message": "规则更新功能尚未完全实现"}
            except json.JSONDecodeError:
                return {"success": False, "error": "无效的JSON变量格式"}

        return {"success": False, "error": "规则编辑功能尚未完全实现"}
    except Exception as e:
        logger.error("编辑规则失败: %s", str(e))
        return {"success": False, "error": f"编辑规则失败: {str(e)}"}


def delete_rule(template_manager, args) -> Dict[str, Any]:
    """删除规则

    Args:
        template_manager: 模板管理器
        args: 命令参数

    Returns:
        处理结果
    """
    try:
        rule_id = args.get("id") if isinstance(args, dict) else args.id
        force = (
            args.get("force", False) if isinstance(args, dict) else getattr(args, "force", False)
        )

        # 先检查规则是否存在
        rule = template_manager.get_template(rule_id)
        if not rule:
            logger.error("未找到规则: %s", rule_id)
            return {"success": False, "error": f"未找到规则: {rule_id}"}

        # 如果是危险操作且没有force标志，返回警告
        if not force:
            return {"success": False, "error": f"删除规则是危险操作，请添加--force参数确认执行", "require_force": True}

        success = template_manager.delete_template(rule_id)
        if success:
            logger.info("规则删除成功: %s", rule_id)
            return {"success": True, "message": f"规则删除成功: {rule_id}"}
        else:
            logger.error("删除规则失败: %s", rule_id)
            return {"success": False, "error": f"删除规则失败: {rule_id}"}

    except Exception as e:
        logger.error("删除规则失败: %s", str(e))
        return {"success": False, "error": f"删除规则失败: {str(e)}"}
