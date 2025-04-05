"""
规则命令处理函数
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.cli.commands.rule_command_utils import (
    get_template,
    prepare_variables,
    validate_single_rule,
)
from src.templates.models.template import Template

logger = logging.getLogger(__name__)


def create_rule(template_manager, rule_generator, args) -> int:
    """创建规则"""
    try:
        # 获取参数
        template_type = args.get("template_type") if isinstance(args, dict) else args.template_type
        template_dir = (
            args.get("template_dir")
            if isinstance(args, dict)
            else getattr(args, "template_dir", None)
        )

        # 设置模板目录
        if template_dir:
            template_manager.set_templates_dir(template_dir)

        # 获取模板
        template = get_template(template_manager, template_type)
        if not template:
            logger.error("未找到模板类型: %s", template_type)
            return 1

        # 准备变量
        variables = prepare_variables(args)
        if variables is None:
            return 1

        # 生成规则
        rule = rule_generator.generate_rule(template, variables)

        # 保存规则
        output_dir = (
            args.get("output_dir")
            if isinstance(args, dict)
            else getattr(args, "output_dir", None) or "rules"
        )
        output_path = Path(output_dir) / f"{rule.id}.md"
        rule_generator.generate_rule_file(template, variables, str(output_path))

        logger.info("规则创建成功: %s", output_path)
        return 0

    except Exception as e:
        logger.error("创建规则失败: %s", str(e))
        return 1


def list_rules(template_manager, args) -> int:
    """列出规则"""
    try:
        rules = template_manager.get_all_templates()
        rule_type = args.get("type") if isinstance(args, dict) else getattr(args, "type", None)

        if rule_type:
            rules = [r for r in rules if r.type == rule_type]

        if not rules:
            logger.info("没有找到规则")
            return 0

        for rule in rules:
            print(f"{rule.id}: {rule.name} ({rule.type})")
        return 0

    except Exception as e:
        logger.error("列出规则失败: %s", str(e))
        return 1


def show_rule(template_manager, args) -> int:
    """显示规则详情"""
    try:
        rule_id = args.get("rule_id") if isinstance(args, dict) else args.rule_id
        rule = template_manager.get_template(rule_id)
        if not rule:
            logger.error("未找到规则: %s", rule_id)
            return 1

        print(f"ID: {rule.id}")
        print(f"名称: {rule.name}")
        print(f"类型: {rule.type}")
        print(f"描述: {rule.description}")
        print("\n内容:")
        print(rule.content)
        return 0

    except Exception as e:
        logger.error("显示规则失败: %s", str(e))
        return 1


def edit_rule(template_manager, args) -> int:
    """编辑规则"""
    # TODO: 实现规则编辑功能
    logger.error("规则编辑功能尚未实现")
    return 1


def delete_rule(template_manager, args) -> int:
    """删除规则"""
    try:
        rule_id = args.get("rule_id") if isinstance(args, dict) else args.rule_id
        success = template_manager.delete_template(rule_id)
        if success:
            logger.info("规则删除成功: %s", rule_id)
            return 0
        else:
            logger.error("删除规则失败: %s", rule_id)
            return 1

    except Exception as e:
        logger.error("删除规则失败: %s", str(e))
        return 1


def validate_rule(template_manager, args) -> int:
    """验证规则"""
    try:
        validate_all = args.get("all") if isinstance(args, dict) else getattr(args, "all", False)

        if validate_all:
            rules = template_manager.get_all_templates()
            success = True
            for rule in rules:
                if not validate_single_rule(rule):
                    success = False
            return 0 if success else 1
        else:
            rule_id = args.get("rule_id") if isinstance(args, dict) else args.rule_id
            rule = template_manager.get_template(rule_id)
            if not rule:
                logger.error("未找到规则: %s", rule_id)
                return 1
            return 0 if validate_single_rule(rule) else 1

    except Exception as e:
        logger.error("验证规则失败: %s", str(e))
        return 1


def export_rule(template_manager, args) -> int:
    """导出规则"""
    try:
        rule_id = args.get("rule_id") if isinstance(args, dict) else args.rule_id
        output_path = (
            args.get("output_path")
            if isinstance(args, dict)
            else getattr(args, "output_path", None)
        )

        rule = template_manager.get_template(rule_id)
        if not rule:
            logger.error("未找到规则: %s", rule_id)
            return 1

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rule.content)
            logger.info("规则导出成功: %s -> %s", rule_id, output_path)
        else:
            print(rule.content)

        return 0

    except Exception as e:
        logger.error("导出规则失败: %s", str(e))
        return 1


def import_rule(template_manager, args) -> int:
    """导入规则"""
    try:
        rule_file = args.get("rule_file") if isinstance(args, dict) else args.rule_file
        template = template_manager.import_template_from_file(rule_file)
        if template:
            logger.info("规则导入成功: %s", template.id)
            return 0
        else:
            logger.error("导入规则失败: %s", rule_file)
            return 1

    except Exception as e:
        logger.error("导入规则失败: %s", str(e))
        return 1
