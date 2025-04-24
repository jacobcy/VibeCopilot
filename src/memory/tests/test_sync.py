#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步服务测试脚本

测试知识库同步功能，包括文件同步、知识库导出和内容监控。
"""

import argparse
import logging
import os
import sys
from typing import Any, Dict, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from memory.helpers.sync_tools import export_knowledge_base, get_sync_status, sync_file
from memory.helpers.sync_utils import get_sync_config, update_last_sync_time
from memory.services.sync_service import SyncService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("sync_test.log")],
)

logger = logging.getLogger(__name__)


def test_file_sync(file_path: str, folder: str) -> None:
    """测试单个文件同步"""
    logger.info(f"测试同步文件: {file_path} -> {folder}")

    # 直接使用sync_file函数
    result = sync_file(file_path, folder)

    if result:
        logger.info(f"文件同步成功: {file_path}")
    else:
        logger.error(f"文件同步失败: {file_path}")


def test_rules_sync(service: SyncService) -> None:
    """测试规则同步"""
    logger.info("测试规则同步...")

    success, message, result = service.sync_rules()

    if success:
        logger.info(f"规则同步成功: {message}")
        logger.info(f"成功: {result.get('synced', 0)}个, 失败: {result.get('failed', 0)}个")
    else:
        logger.error(f"规则同步失败: {message}")


def test_documents_sync(service: SyncService, doc_path: str = None) -> None:
    """测试文档同步"""
    logger.info("测试文档同步...")

    # 如果提供了特定文档路径，只同步该文档
    files = [doc_path] if doc_path else None

    success, message, result = service.sync_documents(files)

    if success:
        logger.info(f"文档同步成功: {message}")
        logger.info(f"成功: {result.get('synced', 0)}个, 失败: {result.get('failed', 0)}个")
    else:
        logger.error(f"文档同步失败: {message}")


def test_export(service: SyncService, output_dir: str, format_type: str = "md") -> None:
    """测试知识库导出"""
    logger.info(f"测试知识库导出: 格式={format_type}, 目录={output_dir}")

    success, message, result = service.export_documents(output_dir, format_type)

    if success:
        logger.info(f"知识库导出成功: {message}")
        logger.info(f"导出文件数: {result.get('file_count', 0)}")
        logger.info(f"导出路径: {result.get('export_path', '')}")
    else:
        logger.error(f"知识库导出失败: {message}")


def test_sync_status(service: SyncService) -> None:
    """测试获取同步状态"""
    logger.info("测试获取同步状态...")

    success, message, result = service.get_status()

    if success:
        logger.info(f"获取同步状态成功: {message}")
        logger.info(f"同步配置: {result.get('config', {})}")
    else:
        logger.error(f"获取同步状态失败: {message}")


def test_all(config: Dict[str, Any] = None) -> None:
    """运行所有测试"""
    logger.info("开始全面测试同步功能...")

    # 创建同步服务
    service = SyncService(config)

    # 获取同步状态
    test_sync_status(service)

    # 同步规则
    test_rules_sync(service)

    # 同步文档
    test_documents_sync(service)

    # 测试导出
    output_dir = os.path.expanduser("~/Public/VibeCopilot/temp/export")
    test_export(service, output_dir)

    logger.info("同步功能测试完成")


def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="测试知识库同步功能")

    parser.add_argument("--test", choices=["file", "rules", "docs", "export", "status", "all"], default="all", help="要运行的测试类型")

    parser.add_argument("--file", help="要同步的文件路径")
    parser.add_argument("--folder", default="test", help="同步目标文件夹")
    parser.add_argument("--output", default="~/Public/VibeCopilot/temp/export", help="导出目录")
    parser.add_argument("--format", default="md", help="导出格式")
    parser.add_argument("--project", default="vibecopilot", help="项目名称")

    args = parser.parse_args()

    # 创建配置
    config = {"project": args.project, "memory_root": "/Volumes/Cube/VibeCopilot/.ai/memory", "rules_dir": "rules", "docs_dir": "docs"}

    # 创建同步服务
    service = SyncService(config)

    # 根据测试类型执行不同的测试
    if args.test == "file":
        if not args.file:
            logger.error("必须指定要同步的文件路径")
            parser.print_help()
            return
        test_file_sync(args.file, args.folder)

    elif args.test == "rules":
        test_rules_sync(service)

    elif args.test == "docs":
        test_documents_sync(service, args.file)

    elif args.test == "export":
        output_dir = os.path.expanduser(args.output)
        test_export(service, output_dir, args.format)

    elif args.test == "status":
        test_sync_status(service)

    elif args.test == "all":
        test_all(config)


if __name__ == "__main__":
    main()
