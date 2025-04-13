"""
文档引擎接口模块
提供统一的文档引擎接口，使用src.parsing解析文档文件，并提供格式转换功能
"""

import logging
import os
from typing import Any, Dict, List, Optional

from src.docs_engine.engine import create_document_engine
from src.parsing import create_parser

logger = logging.getLogger(__name__)


def parse_document_file(file_path: str, parser_type: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """解析文档文件

    使用统一的parsing接口解析文档文件

    Args:
        file_path: 文档文件路径
        parser_type: 解析器类型，如不指定则使用默认值
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        Dict: 解析后的文档结构
    """
    logger.info(f"使用parsing模块解析文档文件: {file_path}")

    # 创建解析器
    config = {}
    if model:
        config["model"] = model

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 读取文件内容
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 使用新的parsing接口
    parser = create_parser(content_type="document", backend=parser_type or "openai", config=config)

    # 使用parse_text方法
    # 注意：parse_text是异步方法，需要在异步上下文中调用
    # 这里我们使用一个简单的同步实现
    import asyncio

    try:
        import nest_asyncio

        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(parser.parse_text(content, content_type="document"))
    except Exception as e:
        logger.error(f"调用解析器失败: {str(e)}")
        result = {
            "success": False,
            "error": str(e),
            "content_type": "document",
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
        }

    # 添加文件信息
    result["_file_info"] = {
        "path": file_path,
        "name": os.path.basename(file_path),
        "extension": os.path.splitext(file_path)[1],
        "directory": os.path.dirname(file_path),
    }

    logger.info(f"文档文件解析完成: {file_path}")
    return result


def parse_document_content(content: str, context: str = "", parser_type: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """解析文档内容

    使用统一的parsing接口解析文档内容

    Args:
        content: 文档文本内容
        context: 上下文信息(文件路径等)
        parser_type: 解析器类型，如不指定则使用默认值
        model: 模型名称，如不指定则使用环境变量或默认值

    Returns:
        Dict: 解析后的文档结构
    """
    logger.info(f"使用parsing模块解析文档内容, 上下文: {context}")

    # 创建解析器
    config = {"context": context}
    if model:
        config["model"] = model

    # 使用新的parsing接口
    parser = create_parser(content_type="document", backend=parser_type or "openai", config=config)

    # 判断解析器类型
    if hasattr(parser, "parse"):
        # 如果是LLMParser，使用parse方法
        result = parser.parse(content, content_type="document")
    else:
        # 如果是其他解析器，使用同步方法
        import asyncio

        try:
            import nest_asyncio

            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(parser.parse_text(content, content_type="document"))
        except Exception as e:
            logger.error(f"调用解析器失败: {str(e)}")
            result = {
                "success": False,
                "error": str(e),
                "content_type": "document",
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
            }

    logger.info(f"文档内容解析完成")
    return result


def extract_document_blocks(file_path: str) -> List[Dict[str, Any]]:
    """从文档文件中提取块

    Args:
        file_path: 文档文件路径

    Returns:
        List[Dict[str, Any]]: 提取的块列表
    """
    logger.info(f"从文档中提取块: {file_path}")

    # 解析文档
    doc_data = parse_document_file(file_path)

    # 返回块列表
    blocks = doc_data.get("blocks", [])
    logger.info(f"提取了 {len(blocks)} 个块")
    return blocks


def import_document_to_db(file_path: str) -> Dict[str, Any]:
    """将文档导入到数据库

    Args:
        file_path: 文档文件路径

    Returns:
        Dict[str, Any]: 导入结果
    """
    logger.info(f"导入文档到数据库: {file_path}")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 读取文件内容
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 使用新的parsing接口解析并保存
    parser = create_parser(content_type="document")

    # 使用parse_text方法
    # 注意：parse_text是异步方法，需要在异步上下文中调用
    import asyncio

    try:
        import nest_asyncio

        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        doc_data = loop.run_until_complete(parser.parse_text(content, content_type="document"))
    except Exception as e:
        logger.error(f"调用解析器失败: {str(e)}")
        doc_data = {
            "success": False,
            "error": str(e),
            "content_type": "document",
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
        }

    # 添加文件信息
    doc_data["_file_info"] = {
        "path": file_path,
        "name": os.path.basename(file_path),
        "extension": os.path.splitext(file_path)[1],
        "directory": os.path.dirname(file_path),
    }

    return {
        "success": True,
        "document_id": doc_data.get("id"),
        "title": doc_data.get("title"),
        "block_count": len(doc_data.get("blocks", [])),
        "message": f"文档 '{doc_data.get('title')}' 已成功导入到数据库",
    }


def convert_document_links(content: str, from_format: str, to_format: str) -> str:
    """转换文档中的链接格式

    Args:
        content: 文档内容
        from_format: 源格式 (obsidian, markdown等)
        to_format: 目标格式 (docusaurus, markdown等)

    Returns:
        str: 转换后的文档内容
    """
    logger.info(f"转换文档链接: {from_format} -> {to_format}")

    # 使用文档引擎的链接转换功能
    engine = create_document_engine(os.getcwd())
    result = engine.convert_links(content, from_format, to_format)

    logger.info("链接转换完成")
    return result


def create_document_from_template(template: str, output_path: str, variables: Optional[Dict[str, Any]] = None) -> bool:
    """使用模板创建文档

    Args:
        template: 模板名称
        output_path: 输出路径
        variables: 变量字典

    Returns:
        bool: 是否成功
    """
    logger.info(f"使用模板创建文档: {template} -> {output_path}")

    # 使用文档引擎的模板功能
    engine = create_document_engine(os.getcwd())
    # 确保变量字典不为 None
    vars_dict = variables or {}
    result = engine.generate_new_document(template, output_path, vars_dict)

    logger.info(f"文档创建{'成功' if result else '失败'}")
    return result
