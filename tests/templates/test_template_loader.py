"""
模板加载器单元测试

测试模板加载和管理功能
"""

import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.models.template import Template
from src.templates.core.managers.template_loader import TemplateLoader


class TestTemplateLoader:
    """模板加载器测试类"""

    def setup_method(self):
        """测试准备"""
        self.test_dir = tempfile.mkdtemp()
        self.templates_dir = os.path.join(self.test_dir, "templates")
        os.makedirs(self.templates_dir)

        # 创建测试模板文件
        self.create_test_template_files()

        # 创建模拟的依赖对象
        self.mock_session = MagicMock()
        self.mock_template_repo = MagicMock()
        self.mock_variable_repo = MagicMock()

        # 创建测试实例
        self.template_loader = TemplateLoader(session=self.mock_session, template_repo=self.mock_template_repo, variable_repo=self.mock_variable_repo)

    def teardown_method(self):
        """测试清理"""
        shutil.rmtree(self.test_dir)

    def create_test_template_files(self):
        """创建测试模板文件"""
        # 模板1：带YAML前置信息的Markdown模板
        template1_path = os.path.join(self.templates_dir, "template1.md")
        template1_content = """---
id: test-template-1
name: Test Template 1
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

    @patch("os.path.exists")
    @patch("os.walk")
    def test_load_templates_from_directory(self, mock_walk, mock_exists):
        """测试从目录加载模板"""
        # 模拟目录存在
        mock_exists.return_value = True

        # 模拟os.walk返回值
        mock_walk.return_value = [(self.templates_dir, [], ["template1.md", "template2.j2"])]

        # 模拟_load_single_template方法
        template1 = Template(id="test-template-1", name="Test Template 1", type="agent", description="", content="# {{ title }}")

        template2 = Template(id="template2", name="Template 2", type="code", description="", content="function {{ function_name }}() {}")

        # 使用side_effect替换_load_single_template方法的行为
        with patch.object(self.template_loader, "_load_single_template") as mock_load:
            mock_load.side_effect = [template1, template2]

            # 加载模板
            count = self.template_loader.load_templates_from_directory(self.templates_dir)

            # 验证结果
            assert count == 2
            assert mock_load.call_count == 2

            # 验证调用_load_single_template的参数
            expected_calls = [((os.path.join(self.templates_dir, "template1.md"),),), ((os.path.join(self.templates_dir, "template2.j2"),),)]
            mock_load.assert_has_calls(expected_calls)

    def test_import_template_from_dict(self):
        """测试从字典导入模板"""
        # 创建模板数据
        template_dict = {
            "id": "test-import",
            "name": "Test Import Template",
            "description": "A template imported from dictionary",
            "type": "general",
            "content": "# {{ title }}\n\n{{ content }}",
            "variables": [{"name": "title", "type": "string", "required": True}, {"name": "content", "type": "string", "required": True}],
            "metadata": {"author": "Test Author", "tags": ["test", "import"], "version": "1.0.0"},
        }

        # 模拟数据库操作
        mock_db_template = MagicMock()
        mock_db_template.to_pydantic.return_value = Template(
            id="test-import",
            name="Test Import Template",
            type="general",
            description="A template imported from dictionary",
            content="# {{ title }}\n\n{{ content }}",
        )
        self.mock_template_repo.create_template.return_value = mock_db_template

        # 确保get_template_by_id返回None，表示模板不存在
        self.mock_template_repo.get_template_by_id.return_value = None

        # 导入模板
        result = self.template_loader.import_template_from_dict(template_dict)

        # 验证结果
        assert result.id == "test-import"
        assert result.name == "Test Import Template"
        self.mock_template_repo.create_template.assert_called_once()

    def test_import_template_with_overwrite(self):
        """测试覆盖已存在的模板"""
        # 创建模板数据
        template_dict = {"id": "existing-template", "name": "Existing Template", "type": "general", "content": "Updated content"}

        # 模拟已存在的模板
        mock_existing_template = MagicMock()
        self.mock_template_repo.get_template_by_id.return_value = mock_existing_template

        # 模拟更新后的模板
        mock_updated_template = MagicMock()
        mock_updated_template.to_pydantic.return_value = Template(
            id="existing-template", name="Existing Template", type="general", description="", content="Updated content"
        )
        self.mock_template_repo.create_template.return_value = mock_updated_template

        # 导入模板并覆盖
        result = self.template_loader.import_template_from_dict(template_dict, overwrite=True)

        # 验证结果
        assert result.id == "existing-template"
        self.mock_template_repo.delete_template.assert_called_once_with("existing-template")
        self.mock_template_repo.create_template.assert_called_once()

    def test_import_template_without_overwrite(self):
        """测试不覆盖已存在的模板"""
        # 创建模板数据
        template_dict = {"id": "existing-template", "name": "Existing Template", "type": "general", "content": "New content"}

        # 模拟已存在的模板
        mock_existing_template = MagicMock()
        mock_existing_template.to_pydantic.return_value = Template(
            id="existing-template", name="Existing Template", type="general", description="", content="Original content"
        )
        self.mock_template_repo.get_template_by_id.return_value = mock_existing_template

        # 导入模板但不覆盖
        result = self.template_loader.import_template_from_dict(template_dict, overwrite=False)

        # 验证结果
        assert result.id == "existing-template"
        self.mock_template_repo.delete_template.assert_not_called()
        self.mock_template_repo.create_template.assert_not_called()
