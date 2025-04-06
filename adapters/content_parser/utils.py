"""
工具函数
提供内容解析的工具函数
"""

import logging
import os
from typing import Any, Dict, List, Optional

from adapters.content_parser.parser_factory import create_parser, get_default_parser

# 创建日志记录器
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
            content_type = _detect_content_type(file_path)
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
        _save_to_database(result, content_type)

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
        if content_type == "generic" and context:
            content_type = _detect_content_type(context)
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
        _save_to_database(result, content_type)

        return result
    except Exception as e:
        logger.error(f"内容解析失败, 错误: {str(e)}", exc_info=True)
        raise


def _detect_content_type(file_path: str) -> str:
    """检测内容类型

    Args:
        file_path: 文件路径

    Returns:
        str: 内容类型 ("rule", "document", "generic")
    """
    # 基于文件路径判断内容类型
    lower_path = file_path.lower()

    # 如果在rules目录中，或者以rule.mdc结尾，则为规则
    if "rules/" in lower_path or lower_path.endswith("rule.mdc") or lower_path.endswith("rule.md"):
        return "rule"

    # 如果在docs目录中，则为文档
    if "docs/" in lower_path or "documents/" in lower_path:
        return "document"

    # 否则为通用内容
    return "generic"


def _save_to_database(data: Dict[str, Any], content_type: str) -> None:
    """保存解析结果到数据库

    Args:
        data: 解析后的数据
        content_type: 内容类型 ("rule", "document", "generic")
    """
    try:
        if content_type == "rule":
            _save_rule_to_database(data)
        elif content_type == "document":
            _save_document_to_database(data)
        else:
            logger.info(f"不保存通用内容到数据库: {data.get('id', 'unknown')}")
    except Exception as e:
        logger.error(f"保存到数据库失败: {e}", exc_info=True)


def _save_rule_to_database(rule_data: Dict[str, Any]) -> None:
    """将规则保存到数据库

    Args:
        rule_data: 规则数据
    """
    try:
        # 导入数据库模型
        # 验证规则结构
        from adapters.content_parser.lib.content_template import validate_rule_structure
        from src.models.db import Rule, RuleItem, RuleType

        if not validate_rule_structure(rule_data):
            logger.warning(f"规则结构无效，跳过保存: {rule_data.get('id', 'unknown')}")
            return

        # 获取会话
        from src.workflow.workflow_manager import get_session

        with get_session() as session:
            # 检查规则是否已存在
            rule_id = rule_data.get("id")
            existing_rule = session.query(Rule).filter(Rule.id == rule_id).first()

            if existing_rule:
                logger.info(f"更新现有规则: {rule_id}")
                # 更新规则属性
                existing_rule.name = rule_data.get("name", existing_rule.name)
                existing_rule.description = rule_data.get("description", existing_rule.description)
                existing_rule.type = RuleType(rule_data.get("type", existing_rule.type.value))
                existing_rule.globs = rule_data.get("globs", existing_rule.globs)
                existing_rule.always_apply = rule_data.get(
                    "always_apply", existing_rule.always_apply
                )
                existing_rule.content = rule_data.get("content", existing_rule.content)

                # 清除现有项目
                for item in existing_rule.items:
                    session.delete(item)

                # 添加新项目
                for i, item_data in enumerate(rule_data.get("items", [])):
                    item = RuleItem(
                        rule_id=existing_rule.id,
                        content=item_data.get("content", ""),
                        priority=item_data.get("priority", i + 1),
                        category=item_data.get("category", "general"),
                    )
                    session.add(item)
            else:
                logger.info(f"创建新规则: {rule_id}")
                # 创建新规则
                rule = Rule(
                    id=rule_id,
                    name=rule_data.get("name", rule_id),
                    description=rule_data.get("description", ""),
                    type=RuleType(rule_data.get("type", "manual")),
                    globs=rule_data.get("globs", []),
                    always_apply=rule_data.get("always_apply", False),
                    content=rule_data.get("content", ""),
                )
                session.add(rule)

                # 添加规则项目
                for i, item_data in enumerate(rule_data.get("items", [])):
                    item = RuleItem(
                        rule_id=rule_id,
                        content=item_data.get("content", ""),
                        priority=item_data.get("priority", i + 1),
                        category=item_data.get("category", "general"),
                    )
                    session.add(item)

            # 提交更改
            session.commit()
            logger.info(f"规则已保存到数据库: {rule_id}")

    except Exception as e:
        logger.error(f"将规则保存到数据库失败: {e}", exc_info=True)
        raise


def _save_document_to_database(doc_data: Dict[str, Any]) -> None:
    """将文档保存到数据库

    Args:
        doc_data: 文档数据
    """
    try:
        # 导入数据库模型和API
        # 验证文档结构
        from adapters.content_parser.lib.content_template import validate_document_structure
        from src.docs_engine.api import BlockManager, DocumentEngine
        from src.models.db import Document, DocumentStatus

        if not validate_document_structure(doc_data):
            logger.warning(f"文档结构无效，跳过保存: {doc_data.get('id', 'unknown')}")
            return

        # 获取会话
        from src.workflow.workflow_manager import get_session

        with get_session() as session:
            # 创建DocumentEngine和BlockManager
            document_engine = DocumentEngine(session)
            block_manager = BlockManager(session)

            # 准备文档数据
            title = doc_data.get("title", "")
            path = doc_data.get("path", "")
            metadata = {"description": doc_data.get("description", ""), "source": "content_parser"}

            # 检查文档是否已存在
            existing_doc = document_engine.get_document_by_path(path) if path else None

            if existing_doc:
                logger.info(f"更新现有文档: {title} ({path})")
                # 更新文档
                document_engine.update_document(
                    document_id=existing_doc["id"], title=title, metadata=metadata
                )
                document_id = existing_doc["id"]
            else:
                logger.info(f"创建新文档: {title} ({path})")
                # 创建新文档
                document = document_engine.create_document(
                    title=title, path=path, status=DocumentStatus.DRAFT.value, metadata=metadata
                )
                document_id = document["id"]

            # 处理文档块
            blocks = doc_data.get("blocks", [])
            if blocks:
                logger.info(f"处理文档块: {len(blocks)} 个块")
                # 删除现有块（如果有）
                existing_blocks = block_manager.get_blocks_by_document(document_id)
                for block in existing_blocks:
                    block_manager.delete_block(block["id"])

                # 添加新块
                for i, block_data in enumerate(blocks):
                    block_type = block_data.get("type", "text")
                    block_content = block_data.get("content", "")

                    # 构建元数据
                    block_metadata = {}
                    if block_type == "heading":
                        block_metadata["level"] = block_data.get("level", 1)
                    elif block_type == "code":
                        block_metadata["language"] = block_data.get("language", "text")

                    # 创建块
                    block_manager.create_block(
                        document_id=document_id,
                        content=block_content,
                        type=block_type,
                        sequence=i + 1,
                        metadata=block_metadata,
                    )

            logger.info(f"文档已保存到数据库: {title} ({document_id})")

    except Exception as e:
        logger.error(f"将文档保存到数据库失败: {e}", exc_info=True)
        raise
