#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VibeCopilot Memory标准遵循测试

测试Memory模块是否正确实现了架构规范中定义的标准：
1. permalink格式与处理标准
2. folder路径规范化与层级处理
"""

import logging
import unittest
import uuid
from typing import Any, Dict, List, Tuple

from src.memory import get_memory_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PermalinkStandardsTest(unittest.TestCase):
    """测试permalink格式与处理标准"""

    def setUp(self):
        """测试前准备工作"""
        self.memory_service = get_memory_service()
        # 生成唯一的测试文件夹，避免冲突
        self.test_folder = f"permalink_test_{uuid.uuid4().hex[:8]}"
        self.test_title = f"test_note_{uuid.uuid4().hex[:8]}"
        self.test_content = f"这是一个测试笔记，用于测试permalink标准。创建于{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        """测试后清理工作"""
        try:
            # 删除测试笔记
            self.memory_service.delete_note(path=f"{self.test_folder}/{self.test_title}", force=True)
        except Exception as e:
            logger.warning(f"清理时出错: {e}")

    def test_permalink_format(self):
        """测试permalink格式是否符合标准"""
        # 创建笔记
        success, message, data = self.memory_service.create_note(content=self.test_content, title=self.test_title, folder=self.test_folder)
        self.assertTrue(success, f"创建笔记失败: {message}")

        # 检查返回的permalink是否存在
        self.assertIn("permalink", data, "返回数据中缺少permalink")
        permalink = data["permalink"]

        # 检查permalink格式 - 应该是memory://<folder>/<title>格式
        self.assertTrue(permalink.startswith("memory://"), f"Permalink '{permalink}'不符合标准格式，应以'memory://'开头")

        # 解析permalink中的路径部分
        path_part = permalink[len("memory://") :]
        self.assertEqual(
            f"{self.test_folder}/{self.test_title}", path_part, f"Permalink路径部分'{path_part}'与期望的'{self.test_folder}/{self.test_title}'不匹配"
        )

    def test_permalink_resolution(self):
        """测试permalink解析"""
        # 创建笔记
        success, message, data = self.memory_service.create_note(content=self.test_content, title=self.test_title, folder=self.test_folder)
        self.assertTrue(success, f"创建笔记失败: {message}")
        permalink = data.get("permalink")

        # 使用不同形式的路径引用读取笔记，确保都能被正确解析
        paths_to_test = [
            # 完整permalink
            permalink,
            # 相对路径
            f"{self.test_folder}/{self.test_title}",
            # 标准化后的路径
            f"{self.test_folder}/{self.test_title}",
        ]

        for path in paths_to_test:
            success, message, data = self.memory_service.read_note(path=path)
            self.assertTrue(success, f"使用路径'{path}'读取笔记失败: {message}")
            self.assertEqual(self.test_title, data.get("title"), f"使用路径'{path}'读取的笔记标题不符")

    def test_permalink_stability(self):
        """测试permalink稳定性 - 更新内容不应改变permalink"""
        # 创建笔记
        success, message, data = self.memory_service.create_note(content=self.test_content, title=self.test_title, folder=self.test_folder)
        self.assertTrue(success, f"创建笔记失败: {message}")
        original_permalink = data.get("permalink")

        # 更新笔记内容
        updated_content = f"{self.test_content}\n\n这是更新的内容。"
        success, message, data = self.memory_service.update_note(path=f"{self.test_folder}/{self.test_title}", content=updated_content)
        self.assertTrue(success, f"更新笔记失败: {message}")
        updated_permalink = data.get("permalink")

        # 检查permalink是否保持稳定
        self.assertEqual(original_permalink, updated_permalink, f"更新内容后permalink发生变化，原始: {original_permalink}, 更新后: {updated_permalink}")


class FolderStandardsTest(unittest.TestCase):
    """测试folder路径规范化与层级处理标准"""

    def setUp(self):
        """测试前准备工作"""
        self.memory_service = get_memory_service()
        # 生成基础测试文件夹
        self.base_folder = f"folder_test_{uuid.uuid4().hex[:4]}"
        self.test_content = "这是一个测试笔记，用于测试folder标准。"
        self.created_notes = []  # 记录创建的笔记路径，用于清理

    def tearDown(self):
        """测试后清理工作"""
        for path in self.created_notes:
            try:
                self.memory_service.delete_note(path=path, force=True)
            except Exception as e:
                logger.warning(f"删除笔记'{path}'时出错: {e}")

    def test_folder_normalization(self):
        """测试folder路径规范化"""
        # 测试各种需要规范化的folder形式
        test_cases = [
            # 格式: (输入folder, 期望的规范化folder)
            (f"//{self.base_folder}//", self.base_folder),
            (f"  {self.base_folder}  ", self.base_folder),
            (f"{self.base_folder}\\subfolder", f"{self.base_folder}/subfolder"),
            (f"/{self.base_folder}/", self.base_folder),
        ]

        for input_folder, expected_folder in test_cases:
            title = f"norm_test_{uuid.uuid4().hex[:6]}"
            success, message, data = self.memory_service.create_note(content=self.test_content, title=title, folder=input_folder)
            self.assertTrue(success, f"使用folder '{input_folder}' 创建笔记失败: {message}")

            # 记录创建的笔记路径，用于清理
            self.created_notes.append(f"{expected_folder}/{title}")

            # 验证笔记可以使用规范化后的路径访问
            success, message, data = self.memory_service.read_note(path=f"{expected_folder}/{title}")
            self.assertTrue(success, f"使用规范化路径 '{expected_folder}/{title}' 读取笔记失败: {message}")

            # 验证permalink使用了规范化的folder
            permalink = data.get("permalink", "")
            expected_path = f"memory://{expected_folder}/{title}"
            self.assertEqual(permalink, expected_path, f"Permalink '{permalink}' 不包含规范化的folder路径 '{expected_folder}'")

    def test_folder_hierarchy(self):
        """测试folder层级结构支持"""
        # 创建多级目录结构的笔记
        hierarchy = [
            # (folder, title)
            (f"{self.base_folder}", "root_note"),
            (f"{self.base_folder}/level1", "level1_note"),
            (f"{self.base_folder}/level1/level2", "level2_note"),
            (f"{self.base_folder}/level1/level2/level3", "level3_note"),
            (f"{self.base_folder}/another_branch", "branch_note"),
        ]

        # 创建层级笔记
        for folder, title in hierarchy:
            success, message, data = self.memory_service.create_note(content=f"这是在 {folder} 中的笔记 {title}", title=title, folder=folder)
            self.assertTrue(success, f"在folder '{folder}' 创建笔记 '{title}' 失败: {message}")
            self.created_notes.append(f"{folder}/{title}")

        # 测试列出各级目录
        for folder, _ in hierarchy:
            success, message, notes = self.memory_service.list_notes(folder=folder)
            self.assertTrue(success, f"列出folder '{folder}' 的笔记失败: {message}")

            # 验证只返回直接子项，而非递归返回所有子孙项
            child_count = sum(1 for f, t in hierarchy if f == folder)
            self.assertEqual(len(notes), child_count, f"列出的笔记数量 {len(notes)} 与预期的直接子项数量 {child_count} 不符")

        # 测试搜索特定folder及其子folder
        search_folder = f"{self.base_folder}/level1"
        success, message, results = self.memory_service.search_notes(query="笔记")
        self.assertTrue(success, f"搜索笔记失败: {message}")

        # 验证能够找到相关笔记
        found_titles = [item.get("title") for item in results if item.get("title")]

        # 验证结果中包含下层笔记
        expected_titles = ["level1_note", "level2_note", "level3_note"]
        for title in expected_titles:
            self.assertIn(title, found_titles, f"搜索结果中未包含预期的笔记标题 '{title}'")


class StandardsComplianceTest(unittest.TestCase):
    """综合测试MemoryService实现是否符合标准规范"""

    def test_return_format(self):
        """测试返回格式是否符合标准"""
        memory_service = get_memory_service()

        # 测试几个核心方法的返回值格式
        test_methods = [
            # 无参数方法
            (lambda: memory_service.list_notes(), "list_notes"),
            (lambda: memory_service.sync_all(), "sync_all"),
            # 有参数方法，使用安全值调用
            (lambda: memory_service.search_notes(query="测试"), "search_notes"),
        ]

        for method_call, method_name in test_methods:
            result = method_call()

            # 检查返回值是否是三元组
            self.assertIsInstance(result, tuple, f"{method_name} 的返回值不是元组")
            self.assertEqual(len(result), 3, f"{method_name} 的返回值不是三元组")

            # 检查返回值的三个元素类型
            success, message, data = result
            self.assertIsInstance(success, bool, f"{method_name} 的success不是布尔值")
            self.assertIsInstance(message, str, f"{method_name} 的message不是字符串")
            self.assertIsInstance(data, (dict, list), f"{method_name} 的data既不是字典也不是列表")


def run_standards_tests():
    """运行所有标准遵循测试"""
    permalink_suite = unittest.TestLoader().loadTestsFromTestCase(PermalinkStandardsTest)
    folder_suite = unittest.TestLoader().loadTestsFromTestCase(FolderStandardsTest)
    compliance_suite = unittest.TestLoader().loadTestsFromTestCase(StandardsComplianceTest)

    # 创建测试套件
    all_tests = unittest.TestSuite([permalink_suite, folder_suite, compliance_suite])

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    results = runner.run(all_tests)

    return results.wasSuccessful()


if __name__ == "__main__":
    logging.info("=== VibeCopilot Memory标准遵循测试开始 ===")

    if run_standards_tests():
        print("\n✅ 所有标准遵循测试通过")
        exit(0)
    else:
        print("\n❌ 部分标准遵循测试失败")
        exit(1)
