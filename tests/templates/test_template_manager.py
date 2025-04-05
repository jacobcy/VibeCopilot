"""
模板管理器单元测试
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime

from src.templates.core.template_manager import TemplateManager
from src.templates.models.template import (
    Template,
    TemplateMetadata,
    TemplateVariable,
    TemplateVariableType,
)


class TemplateManagerTests(unittest.TestCase):
    """模板管理器测试类"""

    def setUp(self):
        """测试准备"""
        self.test_dir = tempfile.mkdtemp()
        self.templates_dir = os.path.join(self.test_dir, "templates")
        os.makedirs(self.templates_dir)

        # 创建测试模板文件
        self.create_test_template_files()

        self.template_manager = TemplateManager(templates_dir=self.templates_dir)

    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.test_dir)

    def create_test_template_files(self):
        """创建测试模板文件"""
        # 模板1：带YAML前置信息的Markdown模板
        template1_path = os.path.join(self.templates_dir, "template1.md")
        template1_content = """---
title: Test Template 1
description: A test template with YAML frontmatter
type: agent
author: Test Author
tags: [test, markdown]
version: 1.0.0
---

# {{ title }}

## Description
{{ description }}

## Content
{{ content }}
"""
        with open(template1_path, "w", encoding="utf-8") as f:
            f.write(template1_content)

        # 模板2：Jinja2模板
        template2_path = os.path.join(self.templates_dir, "template2.j2")
        template2_content = """/*
 * {{ title }}
 * Created by: {{ author }}
 * Date: {{ date }}
 */

function {{ function_name }}() {
    // {{ comment }}
    return {{ return_value }};
}
"""
        with open(template2_path, "w", encoding="utf-8") as f:
            f.write(template2_content)

    def test_load_templates_from_directory(self):
        """测试从目录加载模板"""
        # 重新加载模板
        count = self.template_manager.load_templates_from_directory()

        # 验证加载了2个模板
        self.assertEqual(count, 2)

        # 验证模板已加载到缓存
        self.assertEqual(len(self.template_manager.templates_cache), 2)

        # 验证模板1已正确加载
        template1 = self.template_manager.get_template("test-template-1")
        self.assertIsNotNone(template1)
        self.assertEqual(template1.name, "Test Template 1")
        self.assertEqual(template1.type, "agent")
        self.assertEqual(template1.metadata.author, "Test Author")
        self.assertEqual(template1.metadata.tags, ["test", "markdown"])

    def test_get_template(self):
        """测试获取模板"""
        # 先加载模板
        self.template_manager.load_templates_from_directory()

        # 获取存在的模板
        template = self.template_manager.get_template("test-template-1")
        self.assertIsNotNone(template)
        self.assertEqual(template.name, "Test Template 1")

        # 获取不存在的模板
        template = self.template_manager.get_template("non-existent")
        self.assertIsNone(template)

    def test_get_all_templates(self):
        """测试获取所有模板"""
        # 先加载模板
        self.template_manager.load_templates_from_directory()

        # 获取所有模板
        templates = self.template_manager.get_all_templates()

        # 验证返回了2个模板
        self.assertEqual(len(templates), 2)

        # 验证返回的是模板对象列表
        self.assertIsInstance(templates[0], Template)

    def test_add_template(self):
        """测试添加模板"""
        # 创建一个新模板
        template = Template(
            name="New Template",
            description="A new template",
            type="auto",
            content="Hello, {{ name }}!",
            variables=[
                TemplateVariable(
                    name="name",
                    type=TemplateVariableType.STRING,
                    description="The name",
                    required=True,
                )
            ],
            metadata=TemplateMetadata(author="Test Author", tags=["test", "new"], version="1.0.0"),
        )

        # 添加模板
        added_template = self.template_manager.add_template(template)

        # 验证模板ID已设置
        self.assertEqual(added_template.id, "new-template")

        # 验证模板已添加到缓存
        cached_template = self.template_manager.get_template("new-template")
        self.assertIsNotNone(cached_template)
        self.assertEqual(cached_template.name, "New Template")

    def test_update_template(self):
        """测试更新模板"""
        # 先添加一个模板
        template = Template(
            id="test-template",
            name="Test Template",
            description="Original description",
            type="agent",
            content="Original content",
            metadata=TemplateMetadata(author="Original Author", tags=["original"], version="1.0.0"),
        )

        self.template_manager.add_template(template)

        # 更新模板
        update_data = {
            "description": "Updated description",
            "content": "Updated content",
            "metadata": {"tags": ["updated"]},
        }

        updated_template = self.template_manager.update_template("test-template", update_data)

        # 验证模板已更新
        self.assertIsNotNone(updated_template)
        self.assertEqual(updated_template.description, "Updated description")
        self.assertEqual(updated_template.content, "Updated content")
        self.assertEqual(updated_template.metadata.tags, ["updated"])

        # 验证未更新的字段保持不变
        self.assertEqual(updated_template.name, "Test Template")
        self.assertEqual(updated_template.type, "agent")
        self.assertEqual(updated_template.metadata.author, "Original Author")

    def test_delete_template(self):
        """测试删除模板"""
        # 先添加一个模板
        template = Template(
            id="test-template",
            name="Test Template",
            description="A test template",
            type="agent",
            content="Test content",
            metadata=TemplateMetadata(author="Test Author", tags=["test"], version="1.0.0"),
        )

        self.template_manager.add_template(template)

        # 验证模板存在
        self.assertIsNotNone(self.template_manager.get_template("test-template"))

        # 删除模板
        result = self.template_manager.delete_template("test-template")

        # 验证删除成功
        self.assertTrue(result)

        # 验证模板已删除
        self.assertIsNone(self.template_manager.get_template("test-template"))

        # 尝试删除不存在的模板
        result = self.template_manager.delete_template("non-existent")

        # 验证删除失败
        self.assertFalse(result)

    def test_search_templates(self):
        """测试搜索模板"""
        # 添加测试模板
        template1 = Template(
            id="template1",
            name="Python Template",
            description="A template for Python",
            type="agent",
            content="Python content",
            metadata=TemplateMetadata(
                author="Author 1", tags=["python", "backend"], version="1.0.0"
            ),
        )

        template2 = Template(
            id="template2",
            name="React Template",
            description="A template for React",
            type="agent",
            content="React content",
            metadata=TemplateMetadata(
                author="Author 2", tags=["react", "frontend"], version="1.0.0"
            ),
        )

        template3 = Template(
            id="template3",
            name="Node.js Template",
            description="A template for Node.js applications",
            type="auto",
            content="Node.js content",
            metadata=TemplateMetadata(author="Author 3", tags=["node", "backend"], version="1.0.0"),
        )

        self.template_manager.add_template(template1)
        self.template_manager.add_template(template2)
        self.template_manager.add_template(template3)

        # 按关键词搜索
        results = self.template_manager.search_templates(query="python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "template1")

        # 按标签搜索
        results = self.template_manager.search_templates(tags=["backend"])
        self.assertEqual(len(results), 2)
        ids = [t.id for t in results]
        self.assertIn("template1", ids)
        self.assertIn("template3", ids)

        # 没有匹配的搜索
        results = self.template_manager.search_templates(query="non-existent")
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
