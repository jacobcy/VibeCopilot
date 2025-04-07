"""
解析函数模块

提供内容解析的主要函数
"""

import logging
import os
from typing import Any, Dict, Optional

from adapters.content_parser.parser_factory import create_parser, get_default_parser
from adapters.content_parser.utils.detector import detect_content_type, detect_content_type_from_text
from adapters.content_parser.utils.storage import save_to_database

logger = logging.getLogger(__name__)


def parse_file(
    file_path: str,
    content_type: str = "generic",
    parser_type: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """解析文件

    Args:
        file_path: 文件路径
        content_type: 内容类型 ("rule", "document", "generic")
        parser_type: 解析器类型，如不指定则使用默认值
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        Dict: 解析后的结构
    """
    logger.info(f"开始解析文件: {file_path}, 内容类型: {content_type}")
    logger.info(f"使用解析器: {parser_type or '默认'}, 模型: {model or '默认'}")

    try:
        # 自动检测内容类型（如果为generic）
        if content_type == "generic":
            content_type = detect_content_type(file_path)
            logger.info(f"检测到内容类型: {content_type}")

        # 获取解析器
        if parser_type:
            parser = create_parser(parser_type, model, content_type)
        else:
            parser = get_default_parser(content_type)

        logger.info(f"使用解析器类型: {parser.__class__.__name__}")

        # 解析文件
        result = parser.parse_file(file_path)
        logger.info(f"文件解析成功: {file_path}")

        # 保存到数据库
        save_to_database(result, content_type)

        return result
    except Exception as e:
        logger.error(f"文件解析失败: {file_path}, 错误: {str(e)}", exc_info=True)
        raise


def parse_content(
    content: str,
    context: str = "",
    content_type: str = "generic",
    parser_type: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """解析内容

    Args:
        content: 文本内容
        context: 上下文信息(文件路径等)
        content_type: 内容类型 ("rule", "document", "generic")
        parser_type: 解析器类型，如不指定则使用默认值
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        Dict: 解析后的结构
    """
    logger.info(f"开始解析内容, 上下文: {context}, 内容类型: {content_type}")
    logger.info(f"使用解析器: {parser_type or '默认'}, 模型: {model or '默认'}")

    try:
        # 自动检测内容类型（如果为generic）
        if content_type == "generic" and (context or content):
            if context:
                content_type = detect_content_type(context)
            else:
                content_type = detect_content_type_from_text(content)
            logger.info(f"检测到内容类型: {content_type}")

        # 获取解析器
        if parser_type:
            parser = create_parser(parser_type, model, content_type)
        else:
            parser = get_default_parser(content_type)

        logger.info(f"使用解析器类型: {parser.__class__.__name__}")

        # 解析内容
        result = parser.parse_content(content, context)
        logger.info("内容解析成功")

        # 保存到数据库
        save_to_database(result, content_type)

        return result
    except Exception as e:
        logger.error(f"内容解析失败, 错误: {str(e)}", exc_info=True)
        raise
