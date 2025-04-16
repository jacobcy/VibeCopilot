#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VibeCopilot MemoryService接口测试

此测试用例验证MemoryService接口的一致性和功能性，
确保所有命令都只使用MemoryService统一接口。
"""

import logging
import unittest
import uuid
from typing import Any, Dict, List, Optional, Tuple

from src.memory import MemoryService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryServiceTest(unittest.TestCase):
    """MemoryService接口测试类"""

    def setUp(self):
        """测试前准备工作"""
        # 创建MemoryService实例
        self.memory_service = MemoryService()

        # 生成唯一的测试数据
        self.test_folder = f"test_interface_{uuid.uuid4().hex[:8]}"
        self.test_title = f"test_note_{uuid.uuid4().hex[:8]}"
        self.test_content = f"这是一个测试内容。创建于{uuid.uuid4().hex[:8]}。"
        self.test_tags = "测试,interface,api"
        self.test_path = f"{self.test_folder}/{self.test_title}"

    def tearDown(self):
        """测试后清理工作"""
        try:
            # 尝试删除测试创建的笔记
            self.memory_service.delete_note(path=self.test_path, force=True)
        except Exception as e:
            logger.warning(f"清理时出错 (可能是测试已经删除笔记): {e}")

    def test_crud_operations(self):
        """测试基本的CRUD操作"""
        # 1. 创建笔记
        success, message, data = self.memory_service.create_note(
            content=self.test_content, title=self.test_title, folder=self.test_folder, tags=self.test_tags
        )
        self.assertTrue(success, f"创建笔记失败: {message}")
        logger.info(f"创建笔记成功: {message}")

        # 2. 读取笔记
        success, message, data = self.memory_service.read_note(path=self.test_path)
        self.assertTrue(success, f"读取笔记失败: {message}")
        self.assertIn(self.test_content, data.get("content", ""), "读取的内容不匹配")
        logger.info(f"读取笔记成功: {data.get('title')}")

        # 3. 更新笔记
        updated_content = f"{self.test_content}\n\n这是更新的内容。"
        success, message, data = self.memory_service.update_note(path=self.test_path, content=updated_content)
        self.assertTrue(success, f"更新笔记失败: {message}")
        logger.info(f"更新笔记成功: {message}")

        # 验证更新
        success, message, data = self.memory_service.read_note(path=self.test_path)
        self.assertTrue(success, f"读取更新后的笔记失败: {message}")
        self.assertIn("这是更新的内容", data.get("content", ""), "更新的内容不匹配")

        # 4. 删除笔记
        success, message, data = self.memory_service.delete_note(path=self.test_path, force=True)
        self.assertTrue(success, f"删除笔记失败: {message}")
        logger.info(f"删除笔记成功: {message}")

        # 验证删除
        success, message, data = self.memory_service.read_note(path=self.test_path)
        self.assertFalse(success, "删除后仍能读取笔记")

    def test_search_and_list(self):
        """测试搜索和列表功能"""
        # 先创建一个笔记用于测试
        unique_keyword = f"unique_keyword_{uuid.uuid4().hex[:8]}"
        test_content = f"{self.test_content} {unique_keyword}"

        success, message, data = self.memory_service.create_note(
            content=test_content, title=self.test_title, folder=self.test_folder, tags=self.test_tags
        )
        self.assertTrue(success, f"创建测试笔记失败: {message}")

        # 1. 测试列表功能
        success, message, data = self.memory_service.list_notes(folder=self.test_folder)
        self.assertTrue(success, f"列出笔记失败: {message}")
        self.assertGreaterEqual(len(data), 1, "列表结果为空")

        found = False
        for item in data:
            if item.get("title") == self.test_title:
                found = True
                break
        self.assertTrue(found, f"未在列表中找到测试笔记: {self.test_title}")
        logger.info(f"列出笔记成功，找到 {len(data)} 个结果")

        # 2. 测试搜索功能
        success, message, data = self.memory_service.search_notes(query=unique_keyword)
        self.assertTrue(success, f"搜索笔记失败: {message}")

        found = False
        for item in data:
            if item.get("title") == self.test_title:
                found = True
                break
        self.assertTrue(found, f"搜索结果中未找到测试笔记: {self.test_title}")
        logger.info(f"搜索笔记成功，找到 {len(data)} 个结果")

    def test_sync_operations(self):
        """测试同步操作"""
        # 测试同步功能
        success, message, data = self.memory_service.sync_all()
        self.assertTrue(success, f"同步知识库失败: {message}")
        logger.info(f"同步知识库成功: {message}")

        # 测试统计功能
        stats = self.memory_service.get_memory_stats()
        self.assertIsNotNone(stats, "获取统计信息失败")
        self.assertIsInstance(stats, dict, "统计信息类型错误")
        logger.info(f"获取统计信息成功: {stats}")


# 检查接口完整性
def test_interface_completeness():
    """检查MemoryService接口完整性"""
    memory_service = MemoryService()

    # 核心方法列表
    required_methods = [
        "create_note",
        "read_note",
        "update_note",
        "delete_note",
        "list_notes",
        "search_notes",
        "sync_all",
        "start_sync_watch",
        "import_documents",
        "export_documents",
        "get_memory_stats",
    ]

    # 验证是否实现了所有必需的方法
    missing_methods = []
    for method in required_methods:
        if not hasattr(memory_service, method) or not callable(getattr(memory_service, method)):
            missing_methods.append(method)

    if missing_methods:
        raise AssertionError(f"MemoryService缺少以下必需方法: {', '.join(missing_methods)}")
    else:
        print("✅ MemoryService实现了所有必需方法")

    # 检查返回值格式是否符合标准
    test_path = "test_folder/test_note"
    test_content = "测试内容"

    # 测试create_note方法的返回格式
    result = memory_service.create_note(content=test_content, title="test_note", folder="test_folder")
    _validate_result_format(result, "create_note")

    # 删除测试创建的笔记
    memory_service.delete_note(path=test_path, force=True)

    print("✅ MemoryService方法返回值格式符合标准")


def _validate_result_format(result, method_name):
    """验证方法返回值格式是否符合标准"""
    if not isinstance(result, tuple) or len(result) != 3:
        raise AssertionError(f"{method_name} 方法返回值不是三元组 (success, message, data)")

    success, message, data = result

    if not isinstance(success, bool):
        raise AssertionError(f"{method_name} 方法的success不是布尔值")

    if not isinstance(message, str):
        raise AssertionError(f"{method_name} 方法的message不是字符串")

    if not isinstance(data, (dict, list)) and data is not None:
        raise AssertionError(f"{method_name} 方法的data不是字典、列表或None")


if __name__ == "__main__":
    # 先检查接口完整性
    try:
        test_interface_completeness()
    except AssertionError as e:
        print(f"❌ 接口检查失败: {e}")
        exit(1)

    # 运行单元测试
    unittest.main()
