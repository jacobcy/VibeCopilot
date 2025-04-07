"""
规则引擎适配层
用于对接rule_parser模块，解析规则文件
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from src.core.exceptions import RuleError

logger = logging.getLogger(__name__)

# 尝试加载.env文件
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
if env_path.exists():
    logger.info(f"从{env_path}加载环境变量")
    load_dotenv(str(env_path))
else:
    logger.warning(f"未找到.env文件: {env_path}")


def _ensure_parser_available():
    """确保规则解析器可用

    检查rule_parser模块是否可用，如不可用则尝试添加路径
    """
    try:
        import adapters.rule_parser

        logger.debug("规则解析器已导入")
        return True
    except ImportError as e:
        logger.warning(f"无法直接导入规则解析器: {e}")

        # 尝试添加adapters路径
        project_root = Path(__file__).parent.parent.parent
        adapters_path = project_root / "adapters"

        if adapters_path.exists():
            logger.info(f"尝试添加适配器路径: {adapters_path}")
            sys.path.append(str(adapters_path))
            try:
                import adapters.rule_parser

                logger.info("成功导入规则解析器(通过项目根路径)")
                return True
            except ImportError as e2:
                logger.warning(f"通过项目根路径导入失败: {e2}")

        # 尝试查找备选路径
        alt_path = Path(os.path.expanduser("~")) / "Public" / "VibeCopilot" / "adapters"
        if alt_path.exists():
            logger.info(f"尝试添加备选路径: {alt_path}")
            sys.path.append(str(alt_path))
            try:
                import adapters.rule_parser  # noqa: F811

                logger.info("成功导入规则解析器(通过备选路径)")
                return True
            except ImportError as e3:
                logger.warning(f"通过备选路径导入失败: {e3}")

        logger.error("所有尝试导入规则解析器的方法均失败")
        return False


def parse_markdown_rule(file_path: str) -> Dict[str, Any]:
    """解析Markdown格式的规则文件

    Args:
        file_path: 规则文件路径

    Returns:
        Dict[str, Any]: 解析后的规则结构

    Raises:
        RuleError: 规则解析失败
    """
    logger.info(f"开始解析Markdown规则文件: {file_path}")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        error_msg = f"规则文件不存在: {file_path}"
        logger.error(error_msg)
        raise RuleError(error_msg, "E202")

    # 检查环境变量
    parser_type = os.environ.get("VIBE_RULE_PARSER", "openai")
    if parser_type == "openai" and not os.environ.get("OPENAI_API_KEY"):
        warning_msg = "未设置OPENAI_API_KEY环境变量，尝试回退到Ollama解析器"
        logger.warning(warning_msg)
        print(f"警告: {warning_msg}")
        parser_type = "ollama"
        os.environ["VIBE_RULE_PARSER"] = "ollama"

    if not _ensure_parser_available():
        error_msg = "规则解析器不可用，请检查安装"
        logger.error(error_msg)
        raise RuleError(error_msg, "E203")

    try:
        from adapters.rule_parser.utils import parse_rule_file

        logger.info(f"使用 {parser_type} 解析器解析规则")
        parsed_rule = parse_rule_file(file_path)

        # 转换为当前规则引擎期望的格式
        converted_rule = _convert_to_engine_format(parsed_rule, file_path)
        logger.info(f"规则解析成功: {parsed_rule.get('id', '未知ID')}")
        return converted_rule
    except Exception as e:
        error_msg = f"解析规则失败: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuleError(error_msg, "E204")


def _convert_to_engine_format(parsed_rule: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """将解析的规则转换为规则引擎期望的格式

    Args:
        parsed_rule: 解析后的规则
        file_path: 规则文件路径

    Returns:
        Dict[str, Any]: 转换后的规则定义
    """
    logger.debug(f"开始转换规则格式: {parsed_rule.get('id', '未知ID')}")

    try:
        # 构建基础规则
        rule_def = {
            "name": parsed_rule.get("id") or parsed_rule.get("name") or Path(file_path).stem,
            "pattern": parsed_rule.get("pattern", parsed_rule.get("name", "")),
            "action": {},
        }

        # 处理规则模式
        if "globs" in parsed_rule and parsed_rule["globs"]:
            rule_def["globs"] = parsed_rule["globs"]

        # 添加优先级
        if "priority" in parsed_rule:
            rule_def["priority"] = parsed_rule["priority"]

        # 处理规则类型和始终应用
        if "type" in parsed_rule:
            rule_def["type"] = parsed_rule["type"]
        if "always_apply" in parsed_rule:
            rule_def["always_apply"] = parsed_rule["always_apply"]

        # 处理规则描述
        if "description" in parsed_rule:
            rule_def["description"] = parsed_rule["description"]

        # 处理规则项
        if "items" in parsed_rule and parsed_rule["items"]:
            rules_items = []
            for item in parsed_rule["items"]:
                if isinstance(item, dict) and "content" in item:
                    item_def = {"content": item["content"]}

                    # 添加优先级和分类
                    if "priority" in item:
                        item_def["priority"] = item["priority"]
                    if "category" in item:
                        item_def["category"] = item["category"]

                    rules_items.append(item_def)

            if rules_items:
                rule_def["items"] = rules_items

        # 处理示例
        if "examples" in parsed_rule and parsed_rule["examples"]:
            rule_def["examples"] = parsed_rule["examples"]

        # 处理操作
        # 如果规则定义了动作，添加到action字段
        if "action" in parsed_rule and isinstance(parsed_rule["action"], dict):
            rule_def["action"] = parsed_rule["action"]
        else:
            # 构建一个默认的动作
            rule_def["action"] = {"type": "apply_rule", "content": parsed_rule.get("content", "")}

        logger.debug("规则格式转换成功")
        return rule_def
    except Exception as e:
        logger.error(f"规则格式转换失败: {e}", exc_info=True)
        raise RuleError(f"规则格式转换失败: {e}", "E205")
