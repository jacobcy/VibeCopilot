#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
笔记服务测试脚本

测试笔记服务的CRUD功能和本地缓存机制。
"""

import argparse
import logging
import os
import sys
import tempfile
import uuid
from typing import Any, Dict

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from memory.helpers.note_utils import create_note, delete_note, read_note, update_note
from memory.services.note_service import NoteService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("note_test.log")],
)

logger = logging.getLogger(__name__)


def test_create_note(service: NoteService, title: str, content: str, folder: str) -> Dict[str, Any]:
    """测试创建笔记"""
    logger.info(f"测试创建笔记: {title}")

    # 创建笔记
    success, message, result = service.create_note(content, title, folder)

    if success:
        logger.info(f"创建笔记成功: {message}")
        logger.info(f"笔记ID: {result.get('permalink', 'Unknown')}")
    else:
        logger.error(f"创建笔记失败: {message}")

    return result


def test_read_note(service: NoteService, path: str, use_local: bool = True) -> Dict[str, Any]:
    """测试读取笔记"""
    logger.info(f"测试读取笔记: {path}, 使用本地: {use_local}")

    # 读取笔记
    success, content, metadata = service.read_note(path, use_local)

    if success:
        logger.info(f"读取笔记成功: {metadata.get('title', 'Unknown')}")
        logger.info(f"内容长度: {len(content)} 字符")
        logger.info(f"来源: {metadata.get('source', 'Unknown')}")
    else:
        logger.error(f"读取笔记失败: {content}")

    return metadata


def test_update_note(service: NoteService, path: str, new_content: str) -> Dict[str, Any]:
    """测试更新笔记"""
    logger.info(f"测试更新笔记: {path}")

    # 更新笔记
    success, message, result = service.update_note(path, new_content)

    if success:
        logger.info(f"更新笔记成功: {message}")
    else:
        logger.error(f"更新笔记失败: {message}")

    return result


def test_delete_note(service: NoteService, path: str, force: bool = False) -> Dict[str, Any]:
    """测试删除笔记"""
    logger.info(f"测试删除笔记: {path}, 强制: {force}")

    # 删除笔记
    success, message, result = service.delete_note(path, force)

    if success:
        logger.info(f"删除笔记成功: {message}")
    else:
        logger.error(f"删除笔记失败: {message}")

    return result


def test_search_notes(service: NoteService, query: str, use_local: bool = True) -> Dict[str, Any]:
    """测试搜索笔记"""
    logger.info(f"测试搜索笔记: {query}, 使用本地: {use_local}")

    # 搜索笔记
    success, message, results = service.search_notes(query, use_local)

    if success:
        logger.info(f"搜索笔记成功: {message}")
        logger.info(f"结果数量: {len(results)}")

        for i, result in enumerate(results[:5]):  # 只显示前5条
            logger.info(f"结果 {i+1}: {result.get('title', 'Unknown')} - {result.get('folder', 'Unknown')}")
    else:
        logger.error(f"搜索笔记失败: {message}")

    return {"message": message, "results": results}


def test_crud_flow(config: Dict[str, Any] = None) -> None:
    """测试完整的CRUD流程"""
    logger.info("开始测试笔记CRUD流程...")

    # 创建服务
    service = NoteService(config)

    # 生成唯一的测试标题
    test_id = str(uuid.uuid4())[:8]
    title = f"测试笔记_{test_id}"
    content = f"这是一个测试笔记，ID: {test_id}\n\n这是正文内容。"
    folder = "test"

    # 1. 创建笔记
    result = test_create_note(service, title, content, folder)
    permalink = result.get("permalink")

    if not permalink:
        logger.error("测试失败: 无法获取笔记permalink")
        return

    # 2. 读取笔记（从远程）
    logger.info("测试从远程读取笔记...")
    metadata = test_read_note(service, permalink, use_local=False)

    # 3. 读取笔记（从本地缓存）
    logger.info("测试从本地缓存读取笔记...")
    metadata = test_read_note(service, permalink, use_local=True)

    # 4. 更新笔记
    new_content = f"{content}\n\n这是更新后的内容，更新时间: {uuid.uuid4()}"
    result = test_update_note(service, permalink, new_content)

    # 5. 再次读取确认更新成功
    updated_metadata = test_read_note(service, permalink)

    # 6. 搜索笔记
    search_results = test_search_notes(service, test_id)

    # 7. 删除笔记
    delete_result = test_delete_note(service, permalink)

    # 8. 验证删除成功
    try:
        logger.info("验证笔记已删除...")
        deleted_check = test_read_note(service, permalink)
        logger.warning(f"笔记可能未完全删除，仍然可以读取到: {deleted_check.get('title')}")
    except:
        logger.info("验证成功: 笔记已删除")

    logger.info("笔记CRUD流程测试完成")


def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="测试笔记服务功能")

    parser.add_argument("--test", choices=["create", "read", "update", "delete", "search", "crud"], default="crud", help="要运行的测试类型")

    parser.add_argument("--title", help="笔记标题")
    parser.add_argument("--content", help="笔记内容")
    parser.add_argument("--folder", default="test", help="笔记文件夹")
    parser.add_argument("--path", help="笔记路径或标识符")
    parser.add_argument("--query", help="搜索关键词")
    parser.add_argument("--force", action="store_true", help="强制删除")
    parser.add_argument("--use-local", action="store_true", default=True, help="使用本地缓存")
    parser.add_argument("--project", default="vibecopilot", help="项目名称")

    args = parser.parse_args()

    # 创建配置
    config = {"project": args.project, "memory_root": os.path.expanduser("/Volumes/Cube/VibeCopilot/.ai/memory")}

    # 创建服务
    service = NoteService(config)

    # 根据测试类型执行不同的测试
    if args.test == "create":
        if not args.title or not args.content:
            logger.error("创建笔记需要指定标题和内容")
            parser.print_help()
            return
        test_create_note(service, args.title, args.content, args.folder)

    elif args.test == "read":
        if not args.path:
            logger.error("读取笔记需要指定路径")
            parser.print_help()
            return
        test_read_note(service, args.path, args.use_local)

    elif args.test == "update":
        if not args.path or not args.content:
            logger.error("更新笔记需要指定路径和新内容")
            parser.print_help()
            return
        test_update_note(service, args.path, args.content)

    elif args.test == "delete":
        if not args.path:
            logger.error("删除笔记需要指定路径")
            parser.print_help()
            return
        test_delete_note(service, args.path, args.force)

    elif args.test == "search":
        if not args.query:
            logger.error("搜索笔记需要指定关键词")
            parser.print_help()
            return
        test_search_notes(service, args.query, args.use_local)

    elif args.test == "crud":
        test_crud_flow(config)


if __name__ == "__main__":
    main()
