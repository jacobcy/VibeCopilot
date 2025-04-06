"""
模板管理器单元测试
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

# 使用原始Pydantic模型来运行测试
from src.models.template import Template, TemplateMetadata, TemplateVariable, TemplateVariableType
from src.templates.core.template_manager import TemplateManager


class TemplateManagerTests(unittest.TestCase):
    """模板管理器测试类"""

    def setUp(self):
        """测试准备"""
        self.test_dir = tempfile.mkdtemp()
        self.templates_dir = os.path.join(self.test_dir, "templates")
        os.makedirs(self.templates_dir)

        # 创建测试模板文件
        self.create_test_template_files()

        # 创建一个模拟的SQLAlchemy会话
        self.mock_session = MagicMock()
        self.template_manager = TemplateManager(
            session=self.mock_session, templates_dir=self.templates_dir
        )

        # 模拟TemplateRepository和TemplateVariableRepository
        self.template_manager.template_repo = MagicMock()
        self.template_manager.variable_repo = MagicMock()

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

    @patch("src.templates.core.template_manager.TemplateRepository")
    @patch("src.templates.core.template_manager.TemplateVariableRepository")
    def test_load_templates_from_directory(self, mock_var_repo, mock_template_repo):
        """测试从目录加载模板"""
        # 设置模拟返回值
        mock_db_template = MagicMock()
        mock_db_template.to_pydantic.return_value = MagicMock(
            id="test-template-1",
            name="Test Template 1",
            type="agent",
            metadata=MagicMock(author="Test Author", tags=["test", "markdown"]),
        )
        self.template_manager.template_repo.create_template.return_value = mock_db_template

        # 重新加载模板
        count = self.template_manager.load_templates_from_directory()

        # 验证模板已加载到缓存
        self.assertEqual(len(self.template_manager.templates_cache), 2)

        # 验证模板1已正确加载
        template1 = self.template_manager.templates_cache.get("test-template-1")
        self.assertIsNotNone(template1)
        self.assertEqual(template1.name, "Test Template 1")
        self.assertEqual(template1.type, "agent")

    def test_get_template(self):
        """测试获取模板"""
        # 设置模拟数据
        mock_template = MagicMock(id="test-template-1", name="Test Template 1")
        mock_db_template = MagicMock()
        mock_db_template.to_pydantic.return_value = mock_template

        # 设置仓库方法返回值
        self.template_manager.template_repo.get_by_id.return_value = mock_db_template

        # 获取模板 - 应该从数据库中获取
        template = self.template_manager.get_template("test-template-1")
        self.assertIsNotNone(template)
        self.assertEqual(template.name, "Test Template 1")

        # 验证调用了仓库的get_by_id方法
        self.template_manager.template_repo.get_by_id.assert_called_once_with("test-template-1")

        # 再次获取同一个模板 - 应该从缓存中获取
        self.template_manager.template_repo.get_by_id.reset_mock()
        cached_template = self.template_manager.get_template("test-template-1")
        self.assertEqual(cached_template, template)

        # 验证没有再次调用仓库的get_by_id方法
        self.template_manager.template_repo.get_by_id.assert_not_called()

        # 获取不存在的模板
        self.template_manager.template_repo.get_by_id.return_value = None
        template = self.template_manager.get_template("non-existent")
        self.assertIsNone(template)

    def test_get_all_templates(self):
        """测试获取所有模板"""
        # 设置模拟数据
        mock_db_templates = [MagicMock(id="template1"), MagicMock(id="template2")]
        mock_db_templates[0].to_pydantic.return_value = MagicMock(id="template1")
        mock_db_templates[1].to_pydantic.return_value = MagicMock(id="template2")

        # 设置仓库方法返回值
        self.template_manager.template_repo.get_all.return_value = mock_db_templates

        # 获取所有模板
        templates = self.template_manager.get_all_templates()

        # 验证返回了2个模板
        self.assertEqual(len(templates), 2)

        # 验证模板被添加到缓存
        self.assertEqual(len(self.template_manager.templates_cache), 2)

    def test_add_template(self):
        """测试添加模板"""
        # 创建一个新模板
        template = Template(
            id="new-template",
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

        # 设置模拟返回值
        mock_db_template = MagicMock()
        mock_db_template.to_pydantic.return_value = template
        self.template_manager.template_repo.create_template.return_value = mock_db_template

        # 添加模板
        added_template = self.template_manager.add_template(template)

        # 验证模板ID已设置
        self.assertEqual(added_template.id, "new-template")

        # 验证模板已添加到缓存
        self.assertEqual(self.template_manager.templates_cache["new-template"], template)

    def test_update_template(self):
        """测试更新模板"""
        # 先添加一个模拟模板
        mock_template = MagicMock(
            id="test-template",
            name="Test Template",
            description="Original description",
            type="agent",
            content="Original content",
            metadata=MagicMock(author="Original Author", tags=["original"], version="1.0.0"),
        )

        # 设置更新后的模拟模板
        updated_mock_template = MagicMock(
            id="test-template",
            name="Test Template",
            description="Updated description",
            type="agent",
            content="Updated content",
            metadata=MagicMock(author="Original Author", tags=["updated"], version="1.0.0"),
        )

        # 设置模拟返回值
        self.template_manager.template_repo.get_by_id.return_value = mock_template
        self.template_manager.template_repo.update.return_value = mock_template
        mock_template.to_pydantic.return_value = updated_mock_template

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

    def test_delete_template(self):
        """测试删除模板"""
        # 设置模拟数据
        self.template_manager.templates_cache["test-template"] = MagicMock()
        self.template_manager.template_repo.delete.return_value = True

        # 删除模板
        result = self.template_manager.delete_template("test-template")

        # 验证删除成功
        self.assertTrue(result)

        # 验证已从缓存中删除
        self.assertNotIn("test-template", self.template_manager.templates_cache)

        # 尝试删除不存在的模板
        self.template_manager.template_repo.delete.return_value = False
        result = self.template_manager.delete_template("non-existent")

        # 验证删除失败
        self.assertFalse(result)

    def test_search_templates(self):
        """测试搜索模板"""
        # 设置模拟数据
        mock_templates = [
            MagicMock(
                id="template1",
                name="Python Template",
                description="A template for Python",
                type="agent",
                content="Python content",
                metadata=MagicMock(tags=["python", "backend"]),
            ),
            MagicMock(
                id="template2",
                name="React Template",
                description="A template for React",
                type="agent",
                content="React content",
                metadata=MagicMock(tags=["react", "frontend"]),
            ),
        ]

        # 转换为Pydantic模型格式
        mock_db_templates = [MagicMock() for _ in mock_templates]
        for i, template in enumerate(mock_templates):
            mock_db_templates[i].to_pydantic.return_value = template

        # 设置仓库方法返回值
        self.template_manager.template_repo.search_by_tags.return_value = mock_db_templates
        self.template_manager.template_repo.get_all.return_value = mock_db_templates

        # 按标签搜索
        results = self.template_manager.search_templates(tags=["backend"])

        # 标签搜索是在TemplateRepository中完成的，所以这里我们只验证调用了仓库方法
        self.template_manager.template_repo.search_by_tags.assert_called_once_with(["backend"])

        # 重置模拟对象
        self.template_manager.template_repo.search_by_tags.reset_mock()

        # 按关键词搜索 - 这是在Python代码中完成的
        results = self.template_manager.search_templates(query="python")

        # 关键词搜索应该先获取所有模板，然后在Python中过滤
        self.template_manager.template_repo.get_all.assert_called_once()


if __name__ == "__main__":
    unittest.main()
