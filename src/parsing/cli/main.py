#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容解析工具命令行接口

提供统一的内容解析命令行接口，支持规则、文档和通用内容解析。
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

from src.parsing import create_parser
from src.parsing.processors.document_processor import DocumentProcessor
from src.parsing.processors.rule_processor import RuleProcessor
from src.utils.file_utils import file_exists, read_text_file

# 设置日志级别
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="VibeCopilot 内容解析工具")

    # 主要子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 解析文件子命令
    parse_file_parser = subparsers.add_parser("parse-file", help="解析文件内容")
    parse_file_parser.add_argument("file_path", help="要解析的文件路径")
    parse_file_parser.add_argument("--type", choices=["rule", "document", "generic"], default="generic", help="内容类型")
    parse_file_parser.add_argument("--backend", choices=["openai", "ollama", "regex"], default="openai", help="解析器后端")
    parse_file_parser.add_argument("--model", help="模型名称")
    parse_file_parser.add_argument("--output", help="输出文件路径")

    # 解析内容子命令
    parse_content_parser = subparsers.add_parser("parse-content", help="解析文本内容")
    parse_content_parser.add_argument("--content", help="要解析的文本内容")
    parse_content_parser.add_argument("--type", choices=["rule", "document", "generic"], default="generic", help="内容类型")
    parse_content_parser.add_argument("--backend", choices=["openai", "ollama", "regex"], default="openai", help="解析器后端")
    parse_content_parser.add_argument("--model", help="模型名称")
    parse_content_parser.add_argument("--context", help="上下文信息")
    parse_content_parser.add_argument("--output", help="输出文件路径")

    # 处理规则子命令
    process_rule_parser = subparsers.add_parser("process-rule", help="处理规则文件")
    process_rule_parser.add_argument("file_path", help="规则文件路径")
    process_rule_parser.add_argument("--output", help="输出文件路径")

    # 处理文档子命令
    process_doc_parser = subparsers.add_parser("process-doc", help="处理文档文件")
    process_doc_parser.add_argument("file_path", help="文档文件路径")
    process_doc_parser.add_argument("--output", help="输出文件路径")

    return parser.parse_args()


def parse_file(args: argparse.Namespace) -> Dict[str, Any]:
    """解析文件内容"""
    # 验证文件是否存在
    if not file_exists(args.file_path):
        logger.error(f"无法读取文件: {args.file_path}")
        sys.exit(1)

    # 创建配置字典
    config = {}
    if args.model:
        config["model"] = args.model

    # 创建解析器并解析文件
    parser = create_parser(args.type, args.backend, config)
    result = parser.parse_file(args.file_path)

    return result


def parse_content(args: argparse.Namespace) -> Dict[str, Any]:
    """解析文本内容"""
    if not args.content:
        # 如果没有提供内容，尝试从标准输入读取
        content = sys.stdin.read().strip()
        if not content:
            logger.error("未提供内容且标准输入为空")
            sys.exit(1)
    else:
        content = args.content

    # 创建配置字典
    config = {}
    if args.model:
        config["model"] = args.model
    if args.context:
        config["context"] = args.context

    # 创建解析器并解析内容
    parser = create_parser(args.type, args.backend, config)
    result = parser.parse_text(content)

    return result


def process_rule(args: argparse.Namespace) -> Dict[str, Any]:
    """处理规则文件"""
    # 验证文件是否存在
    if not file_exists(args.file_path):
        logger.error(f"无法读取文件: {args.file_path}")
        sys.exit(1)

    # 创建规则处理器并处理文件
    processor = RuleProcessor()
    result = processor.process_rule_file(args.file_path)

    return result


def process_document(args: argparse.Namespace) -> Dict[str, Any]:
    """处理文档文件"""
    # 验证文件是否存在
    if not file_exists(args.file_path):
        logger.error(f"无法读取文件: {args.file_path}")
        sys.exit(1)

    # 创建文档处理器并处理文件
    processor = DocumentProcessor()
    result = processor.process_document_file(args.file_path)

    return result


def output_result(result: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """输出结果"""
    if output_path:
        # 写入到文件
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"结果已写入到: {output_path}")
    else:
        # 输出到标准输出
        print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    """主函数"""
    args = parse_args()

    if args.command == "parse-file":
        result = parse_file(args)
    elif args.command == "parse-content":
        result = parse_content(args)
    elif args.command == "process-rule":
        result = process_rule(args)
    elif args.command == "process-doc":
        result = process_document(args)
    else:
        logger.error(f"未知命令: {args.command}")
        sys.exit(1)

    # 输出结果
    output_result(result, getattr(args, "output", None))


if __name__ == "__main__":
    main()
