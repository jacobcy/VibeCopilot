"""
规则导入导出相关处理函数

提供规则导入导出相关功能实现。
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from src.core.config import ConfigManager

# 引入解析和验证模块
from src.parsing.base_parser import BaseParser
from src.parsing.parsers.openai_parser import OpenAIParser

# 使用新的验证器模块
from src.validation import ValidatorFactory

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
        output_path = args.get("output") if isinstance(args, dict) else getattr(args, "output", None)
        format_type = args.get("format", "text") if isinstance(args, dict) else getattr(args, "format", "text")

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

    整合了解析、验证和存储流程，将规则文件解析为结构化数据，验证数据正确性，然后存储到数据库。

    Args:
        template_manager: 模板管理器
        args: 命令参数

    Returns:
        处理结果
    """
    try:
        file_path = args.get("file_path") if isinstance(args, dict) else args.file_path
        overwrite = args.get("overwrite", False) if isinstance(args, dict) else getattr(args, "overwrite", False)

        # 检查文件路径是否存在
        path = Path(file_path)
        if not path.exists():
            logger.error("文件不存在: %s", file_path)
            return {"success": False, "error": f"文件不存在: {file_path}"}

        # 步骤1: 解析规则文件
        parsed_data = None
        extension = path.suffix.lower()

        # 使用适当的解析器
        if extension in [".mdc", ".md"]:
            logger.info(f"使用OpenAI解析器解析文件: {file_path}")
            # 尝试使用LLM解析器解析内容
            config = ConfigManager().get_config()
            parser_config = config.get("parsing", {})
            parser = OpenAIParser(config=parser_config)

            try:
                parsed_data = parser.parse_file(file_path, content_type="rule")
                logger.info(f"解析结果: {parsed_data}")
            except Exception as parse_error:
                logger.warning(f"LLM解析失败: {str(parse_error)}，使用简单解析")
                # 如果LLM解析失败，回退到简单方法
                parsed_data = {
                    "id": path.stem,
                    "name": path.stem,
                    "type": "rule",
                    "description": f"从文件 {path.name} 导入的规则",
                    "content": path.read_text(encoding="utf-8"),
                }
        elif extension in [".json"]:
            # 解析JSON文件
            try:
                content = path.read_text(encoding="utf-8")
                parsed_data = json.loads(content)
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON解析失败: {str(json_error)}")
                return {"success": False, "error": f"JSON解析失败: {str(json_error)}"}
        elif extension in [".yaml", ".yml"]:
            # 使用YAML验证器解析和验证
            try:
                validator = ValidatorFactory.get_validator("yaml")
                validation_result = validator.validate_from_file(str(path))

                if not validation_result.is_valid:
                    error_msg = "\n".join(validation_result.messages)
                    logger.error(f"YAML格式验证失败: {error_msg}")
                    return {"success": False, "error": f"YAML格式验证失败: {error_msg}"}

                parsed_data = validation_result.data
            except Exception as yaml_error:
                logger.error(f"YAML解析失败: {str(yaml_error)}")
                return {"success": False, "error": f"YAML解析失败: {str(yaml_error)}"}
        else:
            # 默认以文本方式处理
            parsed_data = {
                "id": path.stem,
                "name": path.stem,
                "type": "rule",
                "description": f"从文件 {path.name} 导入的规则",
                "content": path.read_text(encoding="utf-8"),
            }

        # 步骤2: 确保解析结果包含必要字段
        if not parsed_data:
            logger.error("解析规则失败: 未能提取有效数据")
            return {"success": False, "error": "解析规则失败: 未能提取有效数据"}

        # 确保有必要的字段
        if "id" not in parsed_data:
            parsed_data["id"] = path.stem

        if "name" not in parsed_data:
            parsed_data["name"] = path.stem

        if "type" not in parsed_data:
            parsed_data["type"] = "rule"

        if "content" not in parsed_data and path.exists():
            # 如果没有content字段，使用文件内容
            parsed_data["content"] = path.read_text(encoding="utf-8")

        # 步骤3: 保存到数据库
        try:
            # 使用模板管理器导入模板
            imported_template = template_manager.loader.import_template_from_dict(parsed_data, overwrite=overwrite)

            if imported_template:
                logger.info("规则导入成功: %s", imported_template.id)
                return {
                    "success": True,
                    "message": f"规则导入成功: {imported_template.id}",
                    "data": {"id": imported_template.id, "name": imported_template.name, "type": imported_template.type},
                }
            else:
                logger.error("导入规则到数据库失败")
                return {"success": False, "error": "导入规则到数据库失败"}

        except Exception as db_error:
            logger.error(f"保存规则到数据库失败: {str(db_error)}")
            return {"success": False, "error": f"保存规则到数据库失败: {str(db_error)}"}

    except Exception as e:
        logger.error("导入规则失败: %s", str(e))
        return {"success": False, "error": f"导入规则失败: {str(e)}"}
