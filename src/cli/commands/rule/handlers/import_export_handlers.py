"""
规则导入导出相关处理函数

提供规则导入导出相关功能实现。
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def export_rule(template_manager, args) -> Dict[str, Any]:
    """导出规则

    Args:
        template_manager: 模板管理器
        args: 命令参数

    Returns:
        处理结果
    """
    try:
        rule_id = args.get("id") if isinstance(args, dict) else args.id
        output_path = (
            args.get("output") if isinstance(args, dict) else getattr(args, "output", None)
        )
        format_type = (
            args.get("format", "text")
            if isinstance(args, dict)
            else getattr(args, "format", "text")
        )

        rule = template_manager.get_template(rule_id)
        if not rule:
            logger.error("未找到规则: %s", rule_id)
            return {"success": False, "error": f"未找到规则: {rule_id}"}

        # 根据格式输出
        if format_type == "json" and not output_path:
            # 如果是JSON格式且没有指定输出路径，返回规则数据
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

        # 输出到文件
        if output_path:
            if format_type == "json":
                # JSON格式输出
                rule_data = {
                    "id": rule.id,
                    "name": rule.name,
                    "type": rule.type,
                    "description": rule.description,
                    "content": rule.content,
                }
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(rule_data, f, ensure_ascii=False, indent=2)
            else:
                # 原始内容输出
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(rule.content)

            logger.info("规则导出成功: %s -> %s", rule_id, output_path)
            return {"success": True, "message": f"规则导出成功: {rule_id} -> {output_path}"}
        else:
            # 直接返回内容
            return {"success": True, "data": rule.content}

    except Exception as e:
        logger.error("导出规则失败: %s", str(e))
        return {"success": False, "error": f"导出规则失败: {str(e)}"}


def import_rule(template_manager, args) -> Dict[str, Any]:
    """导入规则

    Args:
        template_manager: 模板管理器
        args: 命令参数

    Returns:
        处理结果
    """
    try:
        file_path = args.get("file_path") if isinstance(args, dict) else args.file_path
        overwrite = (
            args.get("overwrite", False)
            if isinstance(args, dict)
            else getattr(args, "overwrite", False)
        )

        # 检查文件是否存在
        if not Path(file_path).exists():
            return {"success": False, "error": f"文件不存在: {file_path}"}

        # 导入规则
        template = template_manager.import_template_from_file(file_path, overwrite=overwrite)
        if template:
            logger.info("规则导入成功: %s", template.id)
            return {
                "success": True,
                "message": f"规则导入成功: {template.id}",
                "data": {"id": template.id, "name": template.name},
            }
        else:
            logger.error("导入规则失败: %s", file_path)
            return {"success": False, "error": f"导入规则失败: {file_path}"}

    except Exception as e:
        logger.error("导入规则失败: %s", str(e))
        return {"success": False, "error": f"导入规则失败: {str(e)}"}
