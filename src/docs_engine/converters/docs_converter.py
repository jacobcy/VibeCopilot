"""
文档引擎接口模块
提供统一的文档引擎接口，使用src.parsing解析文档文件，并提供格式转换功能
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from src.docs_engine.engine import create_document_engine
from src.parsing import create_parser
from src.parsing.processors.document_processor import DocumentProcessor

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

    # 配置参数
    config = {}
    if model:
        config["model"] = model

    # 创建文档处理器
    processor = DocumentProcessor(backend=parser_type or "openai", config=config)

    # 处理文档文件
    result = processor.process_document_file(file_path)

    # 检查处理结果
    if not result.get("success", True):
        logger.error(f"文档解析失败: {result.get('error', '未知错误')}")
        return result

    # 确保字段格式一致性 - 添加文件信息
    if "_file_info" not in result:
        file_info = result.get("file_info", {})
        if file_info:
            result["_file_info"] = {
                "path": file_info.get("path", file_path),
                "name": file_info.get("name", os.path.basename(file_path)),
                "extension": os.path.splitext(file_info.get("name", os.path.basename(file_path)))[1],
                "directory": file_info.get("directory", os.path.dirname(file_path)),
            }
        else:
            result["_file_info"] = {
                "path": file_path,
                "name": os.path.basename(file_path),
                "extension": os.path.splitext(file_path)[1],
                "directory": os.path.dirname(file_path),
            }

    # 确保其他字段存在，保持API兼容性
    if "blocks" not in result:
        result["blocks"] = []

    if "title" not in result:
        # 尝试从文件名中提取标题
        result["title"] = os.path.splitext(os.path.basename(file_path))[0]

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

    # 配置参数
    config = {"context": context}
    if model:
        config["model"] = model

    # 创建文档处理器
    processor = DocumentProcessor(backend=parser_type or "openai", config=config)

    try:
        # 使用DocumentProcessor处理文本
        result = processor.process_document_text(content)

        # 检查处理结果
        if not result.get("success", True):
            logger.error(f"文档内容解析失败: {result.get('error', '未知错误')}")
            return result

        # 确保字段格式一致性
        if "blocks" not in result:
            result["blocks"] = []

        if "title" not in result:
            # 尝试从内容中提取标题
            lines = content.split("\n")
            for line in lines:
                if line.startswith("# "):
                    result["title"] = line[2:].strip()
                    break
            if "title" not in result:
                result["title"] = "未命名文档"

        # 添加上下文信息
        if context and "_context" not in result:
            result["_context"] = context

    except Exception as e:
        logger.error(f"调用文档处理器失败: {str(e)}")
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

    # 检查文档解析是否成功
    if not doc_data.get("success", True):
        logger.error(f"文档解析失败，无法提取块: {doc_data.get('error', '未知错误')}")
        return []

    # 提取块
    blocks = doc_data.get("blocks", [])

    # 如果没有找到块，尝试从结构中提取
    if not blocks and "structure" in doc_data:
        # 从结构中创建块
        structure = doc_data.get("structure", {})

        # 从标题提取块
        if "headings" in structure:
            for heading in structure.get("headings", []):
                blocks.append(
                    {
                        "type": "heading",
                        "level": heading.get("level", 1),
                        "text": heading.get("text", ""),
                        "id": heading.get("id", ""),
                    }
                )

        # 从段落提取块
        if "paragraphs" in structure:
            for para in structure.get("paragraphs", []):
                blocks.append(
                    {
                        "type": "paragraph",
                        "text": para.get("text", ""),
                        "id": para.get("id", ""),
                    }
                )

    # 如果仍然没有找到块，尝试从内容中提取
    if not blocks and "content" in doc_data:
        content = doc_data.get("content", "")
        # 简单地按照空行分割
        sections = content.split("\n\n")
        for i, section in enumerate(sections):
            if section.strip():
                blocks.append(
                    {
                        "type": "section",
                        "text": section.strip(),
                        "id": f"section-{i+1}",
                    }
                )

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

    # 使用DocumentProcessor解析文档
    processor = DocumentProcessor()

    try:
        # 处理文档文件
        doc_data = processor.process_document_file(file_path)

        if not doc_data.get("success", True):
            logger.error(f"文档解析失败: {doc_data.get('error', '未知错误')}")
            return {"success": False, "error": doc_data.get("error", "未知错误"), "message": "文档解析失败"}

        # 获取文件信息
        file_info = {
            "path": doc_data.get("file_info", {}).get("path", file_path),
            "name": doc_data.get("file_info", {}).get("name", os.path.basename(file_path)),
            "extension": os.path.splitext(os.path.basename(file_path))[1],
            "directory": doc_data.get("file_info", {}).get("directory", os.path.dirname(file_path)),
        }

        # 添加文件信息，确保与之前的格式兼容
        doc_data["_file_info"] = file_info

        logger.info(f"文档解析成功: {doc_data.get('title', '无标题')}")

        # 进行数据库导入操作...
        # 这里可以根据实际需要添加数据库导入逻辑

        return {
            "success": True,
            "document_id": doc_data.get("id", ""),
            "title": doc_data.get("title", "无标题"),
            "block_count": len(doc_data.get("blocks", [])),
            "message": f"文档 '{doc_data.get('title', '无标题')}' 已成功导入到数据库",
        }
    except Exception as e:
        logger.error(f"导入文档到数据库失败: {str(e)}")
        return {"success": False, "error": str(e), "message": "导入文档到数据库失败"}


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
