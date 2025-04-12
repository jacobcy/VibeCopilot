"""
规则创建相关处理函数

提供规则创建相关功能实现。
"""

import logging
from pathlib import Path
from typing import Any, Dict

from src.cli.commands.rule.utils import get_template, prepare_variables

logger = logging.getLogger(__name__)


def create_rule(template_manager, rule_generator, args) -> Dict[str, Any]:
    """创建规则

    Args:
        template_manager: 模板管理器
        rule_generator: 规则生成器
        args: 命令参数

    Returns:
        处理结果
    """
    try:
        # 获取参数
        template_type = args.get("template_type") if isinstance(args, dict) else args.template_type
        template_dir = args.get("template_dir") if isinstance(args, dict) else getattr(args, "template_dir", None)

        # 获取规则名称
        rule_name = args.get("name") if isinstance(args, dict) else getattr(args, "name", None)
        if not rule_name:
            logger.error("缺少规则名称参数")
            return {"success": False, "error": "缺少规则名称参数"}

        # 设置模板目录
        if template_dir:
            template_manager.set_templates_dir(template_dir)

        # 获取模板
        template = get_template(template_manager, template_type)
        if not template:
            logger.error("未找到模板类型: %s", template_type)
            return {"success": False, "error": f"未找到模板类型: {template_type}"}

        # 准备变量
        variables = prepare_variables(args)
        if variables is None:
            return {"success": False, "error": "准备变量失败"}

        # 确保设置了规则名称
        variables["name"] = rule_name

        # 生成规则
        rule = rule_generator.generate_rule(template, variables)

        # 保存规则
        output_dir = args.get("output_dir") if isinstance(args, dict) else getattr(args, "output_dir", None) or "rules"
        output_path = Path(output_dir) / f"{rule.id}.md"
        rule_generator.generate_rule_file(template, variables, str(output_path))

        logger.info("规则创建成功: %s", output_path)
        return {
            "success": True,
            "message": f"规则创建成功: {output_path}",
            "data": {"id": rule.id, "name": rule.name, "path": str(output_path)},
        }

    except Exception as e:
        logger.error("创建规则失败: %s", str(e))
        return {"success": False, "error": f"创建规则失败: {str(e)}"}
