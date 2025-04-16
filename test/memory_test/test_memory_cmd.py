#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VibeCopilot Memory命令测试脚本

此脚本用于测试VibeCopilot的memory命令是否能正常工作，
测试主要功能包括：创建笔记、读取笔记、更新笔记、删除笔记和搜索笔记。
"""

import os
import subprocess
import unittest
import uuid
from typing import Dict, List, Tuple


class MemoryCommandTest(unittest.TestCase):
    """VibeCopilot Memory命令测试类"""

    def setUp(self):
        """测试前准备工作"""
        # 生成唯一的测试文件夹名，避免冲突
        self.test_folder = f"test_folder_{uuid.uuid4().hex[:8]}"
        # 生成唯一的测试文件名，避免冲突
        self.test_title = f"test_note_{uuid.uuid4().hex[:8]}"
        self.test_content = f"这是一个测试笔记。创建于{uuid.uuid4().hex[:8]}。"
        self.test_tags = "测试,vibecopilot,命令测试"

    def tearDown(self):
        """测试后清理工作，删除测试创建的笔记"""
        try:
            # 查找并删除创建的测试笔记
            self._execute_command(["vibecopilot", "memory", "delete", "--path", f"{self.test_folder}/{self.test_title}", "--force"])
        except Exception:
            pass  # 忽略删除失败，可能是因为测试已经删除了

    def _execute_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """
        执行命令并返回结果

        Args:
            cmd: 要执行的命令列表

        Returns:
            返回码, 标准输出, 错误输出
        """
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr

    def test_create_and_read_note(self):
        """测试创建和读取笔记功能"""
        # 1. 创建笔记
        create_cmd = [
            "vibecopilot",
            "memory",
            "create",
            "--title",
            self.test_title,
            "--folder",
            self.test_folder,
            "--tags",
            self.test_tags,
            "--content",
            self.test_content,
        ]
        code, stdout, stderr = self._execute_command(create_cmd)

        # 验证创建是否成功
        self.assertEqual(code, 0, f"创建笔记失败: {stderr}")
        self.assertIn("内容已保存", stdout, "创建成功消息未显示")

        # 2. 读取笔记
        read_cmd = ["vibecopilot", "memory", "show", "--path", f"{self.test_folder}/{self.test_title}"]
        code, stdout, stderr = self._execute_command(read_cmd)

        # 验证读取是否成功
        self.assertEqual(code, 0, f"读取笔记失败: {stderr}")
        self.assertIn(self.test_content, stdout, "读取的内容与创建的不一致")

    def test_update_note(self):
        """测试更新笔记功能"""
        # 1. 先创建笔记
        create_cmd = [
            "vibecopilot",
            "memory",
            "create",
            "--title",
            self.test_title,
            "--folder",
            self.test_folder,
            "--tags",
            self.test_tags,
            "--content",
            self.test_content,
        ]
        self._execute_command(create_cmd)

        # 2. 更新笔记
        updated_content = f"{self.test_content}\n\n这是更新的内容。"
        update_cmd = ["vibecopilot", "memory", "update", "--path", f"{self.test_folder}/{self.test_title}", "--content", updated_content]
        code, stdout, stderr = self._execute_command(update_cmd)

        # 验证更新是否成功
        self.assertEqual(code, 0, f"更新笔记失败: {stderr}")

        # 3. 读取更新后的笔记
        read_cmd = ["vibecopilot", "memory", "show", "--path", f"{self.test_folder}/{self.test_title}"]
        code, stdout, stderr = self._execute_command(read_cmd)

        # 验证读取更新后的内容
        self.assertEqual(code, 0, f"读取更新后的笔记失败: {stderr}")
        self.assertIn("这是更新的内容", stdout, "更新后的内容未包含新增部分")

    def test_delete_note(self):
        """测试删除笔记功能"""
        # 1. 先创建笔记
        create_cmd = [
            "vibecopilot",
            "memory",
            "create",
            "--title",
            self.test_title,
            "--folder",
            self.test_folder,
            "--tags",
            self.test_tags,
            "--content",
            self.test_content,
        ]
        self._execute_command(create_cmd)

        # 2. 删除笔记
        delete_cmd = ["vibecopilot", "memory", "delete", "--path", f"{self.test_folder}/{self.test_title}", "--force"]
        code, stdout, stderr = self._execute_command(delete_cmd)

        # 验证删除是否成功
        self.assertEqual(code, 0, f"删除笔记失败: {stderr}")

        # 3. 尝试读取已删除的笔记，应该失败
        read_cmd = ["vibecopilot", "memory", "show", "--path", f"{self.test_folder}/{self.test_title}"]
        code, stdout, stderr = self._execute_command(read_cmd)

        # 验证笔记是否已删除
        self.assertNotEqual(code, 0, "已删除的笔记仍然可以读取")

    def test_search_notes(self):
        """测试搜索笔记功能"""
        # 1. 先创建包含特定关键词的笔记
        unique_keyword = f"unique_keyword_{uuid.uuid4().hex[:8]}"
        create_cmd = [
            "vibecopilot",
            "memory",
            "create",
            "--title",
            self.test_title,
            "--folder",
            self.test_folder,
            "--tags",
            self.test_tags,
            "--content",
            f"{self.test_content} {unique_keyword}",
        ]
        self._execute_command(create_cmd)

        # 2. 搜索包含该关键词的笔记
        search_cmd = ["vibecopilot", "memory", "search", "--query", unique_keyword]
        code, stdout, stderr = self._execute_command(search_cmd)

        # 验证搜索是否成功
        self.assertEqual(code, 0, f"搜索笔记失败: {stderr}")
        self.assertIn(self.test_title, stdout, "搜索结果中未包含期望的笔记")

    def test_list_notes(self):
        """测试列出笔记功能"""
        # 1. 先创建笔记
        create_cmd = [
            "vibecopilot",
            "memory",
            "create",
            "--title",
            self.test_title,
            "--folder",
            self.test_folder,
            "--tags",
            self.test_tags,
            "--content",
            self.test_content,
        ]
        self._execute_command(create_cmd)

        # 2. 列出特定文件夹的笔记
        list_cmd = ["vibecopilot", "memory", "list", "--folder", self.test_folder]
        code, stdout, stderr = self._execute_command(list_cmd)

        # 验证列出是否成功
        self.assertEqual(code, 0, f"列出笔记失败: {stderr}")
        self.assertIn(self.test_title, stdout, "列出的笔记中未包含期望的笔记")


if __name__ == "__main__":
    unittest.main()
