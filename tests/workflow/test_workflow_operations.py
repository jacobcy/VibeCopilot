#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工作流基本操作功能
"""

import json
import os
import unittest
from typing import Any, Dict
from unittest.mock import MagicMock, mock_open, patch

from src.workflow.workflow_operations import (
    create_workflow,
    delete_workflow,
    get_workflow,
    get_workflow_by_name,
    get_workflows_directory,
    list_workflows,
    update_workflow,
    view_workflow,
)


class TestWorkflowOperations(unittest.TestCase):
    """测试工作流操作功能"""

    @patch("src.workflow.workflow_operations.get_config")
    def test_get_workflows_directory(self, mock_get_config):
        """测试获取工作流目录路径"""
        mock_config = MagicMock()
        mock_config.get.return_value = "/fake/data/dir"
        mock_get_config.return_value = mock_config

        workflows_dir = get_workflows_directory()

        self.assertEqual(workflows_dir, "/fake/data/dir/workflows")
        mock_get_config.assert_called_once()
        mock_config.get.assert_called_once_with("paths.data_dir", ".")

    @patch("src.workflow.workflow_operations.ensure_directory_exists")
    @patch("src.workflow.workflow_operations.os.listdir")
    @patch("src.workflow.workflow_operations.read_json_file")
    @patch("src.workflow.workflow_operations.get_workflows_directory")
    def test_list_workflows(self, mock_get_dir, mock_read_json, mock_listdir, mock_ensure_dir):
        """测试列出所有工作流"""
        mock_get_dir.return_value = "/fake/workflows/dir"
        mock_listdir.return_value = ["workflow1.json", "workflow2.json", "not_a_workflow.txt"]

        workflow1 = {"id": "workflow1", "name": "Workflow 1"}
        workflow2 = {"id": "workflow2", "name": "Workflow 2"}

        def mock_read_side_effect(path):
            if "workflow1.json" in path:
                return workflow1
            elif "workflow2.json" in path:
                return workflow2
            return None

        mock_read_json.side_effect = mock_read_side_effect

        workflows = list_workflows()

        self.assertEqual(len(workflows), 2)
        self.assertIn(workflow1, workflows)
        self.assertIn(workflow2, workflows)
        mock_listdir.assert_called_once_with("/fake/workflows/dir")
        mock_ensure_dir.assert_called_once_with("/fake/workflows/dir")

    @patch("src.workflow.workflow_operations.file_exists")
    @patch("src.workflow.workflow_operations.read_json_file")
    @patch("src.workflow.workflow_operations.get_workflows_directory")
    def test_get_workflow(self, mock_get_dir, mock_read_json, mock_file_exists):
        """测试通过ID获取工作流"""
        mock_get_dir.return_value = "/fake/workflows/dir"
        workflow_data = {"id": "test-workflow", "name": "Test Workflow"}
        mock_read_json.return_value = workflow_data
        mock_file_exists.return_value = True

        result = get_workflow("test-workflow")

        self.assertEqual(result, workflow_data)
        mock_read_json.assert_called_once_with("/fake/workflows/dir/test-workflow.json")

    @patch("src.workflow.workflow_operations.list_workflows")
    def test_get_workflow_by_name(self, mock_list_workflows):
        """测试通过名称获取工作流"""
        workflows = [{"id": "wf1", "name": "Workflow 1"}, {"id": "wf2", "name": "Workflow 2"}]
        mock_list_workflows.return_value = workflows

        result = get_workflow_by_name("Workflow 2")

        self.assertEqual(result, workflows[1])
        mock_list_workflows.assert_called_once()

    @patch("src.workflow.workflow_operations.list_workflows")
    def test_get_workflow_by_name_not_found(self, mock_list_workflows):
        """测试通过不存在的名称获取工作流"""
        workflows = [{"id": "wf1", "name": "Workflow 1"}, {"id": "wf2", "name": "Workflow 2"}]
        mock_list_workflows.return_value = workflows

        result = get_workflow_by_name("Nonexistent Workflow")

        self.assertIsNone(result)
        mock_list_workflows.assert_called_once()

    @patch("src.workflow.workflow_operations.get_workflow")
    def test_view_workflow(self, mock_get_workflow):
        """测试查看工作流（别名函数）"""
        workflow_data = {"id": "test-workflow", "name": "Test Workflow"}
        mock_get_workflow.return_value = workflow_data

        result = view_workflow("test-workflow")

        self.assertEqual(result, workflow_data)
        mock_get_workflow.assert_called_once_with("test-workflow")

    @patch("src.workflow.workflow_operations.uuid.uuid4")
    @patch("src.workflow.workflow_operations.write_json_file")
    @patch("src.workflow.workflow_operations.get_workflows_directory")
    @patch("src.workflow.workflow_operations.ensure_directory_exists")
    def test_create_workflow(self, mock_ensure_dir, mock_get_dir, mock_write_json, mock_uuid4):
        """测试创建新工作流"""
        mock_get_dir.return_value = "/fake/workflows/dir"
        mock_uuid4.return_value = MagicMock(__str__=lambda x: "generated-uuid")

        workflow_data = {"name": "New Workflow", "description": "Test workflow"}
        expected_data = {"id": "generated-uuid", "name": "New Workflow", "description": "Test workflow"}

        result = create_workflow(workflow_data)

        self.assertEqual(result["id"], "generated-uuid")
        self.assertEqual(result["name"], "New Workflow")
        self.assertEqual(result["description"], "Test workflow")

        mock_ensure_dir.assert_called_once_with("/fake/workflows/dir")
        mock_write_json.assert_called_once()
        # Check that write_json_file was called with correct path
        self.assertEqual(mock_write_json.call_args[0][0], "/fake/workflows/dir/generated-uuid.json")

    @patch("src.workflow.workflow_operations.write_json_file")
    @patch("src.workflow.workflow_operations.get_workflow")
    @patch("src.workflow.workflow_operations.get_workflows_directory")
    def test_update_workflow(self, mock_get_dir, mock_get_workflow, mock_write_json):
        """测试更新已存在的工作流"""
        mock_get_dir.return_value = "/fake/workflows/dir"
        existing_workflow = {"id": "test-workflow", "name": "Old Name", "description": "Old description"}
        mock_get_workflow.return_value = existing_workflow

        update_data = {"name": "New Name", "description": "New description"}

        result = update_workflow("test-workflow", update_data)

        self.assertEqual(result["id"], "test-workflow")
        self.assertEqual(result["name"], "New Name")
        self.assertEqual(result["description"], "New description")

        # Verify write_json_file was called
        mock_write_json.assert_called_once()
        self.assertEqual(mock_write_json.call_args[0][0], "/fake/workflows/dir/test-workflow.json")

    @patch("src.workflow.workflow_operations.get_workflow")
    def test_update_workflow_not_found(self, mock_get_workflow):
        """测试更新不存在的工作流"""
        mock_get_workflow.return_value = None

        result = update_workflow("nonexistent", {"name": "New Name"})

        self.assertIsNone(result)
        mock_get_workflow.assert_called_once_with("nonexistent")

    @patch("src.workflow.workflow_operations.os.remove")
    @patch("src.workflow.workflow_operations.file_exists")
    @patch("src.workflow.workflow_operations.get_workflows_directory")
    def test_delete_workflow(self, mock_get_dir, mock_file_exists, mock_remove):
        """测试删除工作流"""
        mock_get_dir.return_value = "/fake/workflows/dir"
        mock_file_exists.return_value = True

        result = delete_workflow("test-workflow")

        self.assertTrue(result)
        mock_remove.assert_called_once_with("/fake/workflows/dir/test-workflow.json")
        mock_file_exists.assert_called_once_with("/fake/workflows/dir/test-workflow.json")

    @patch("src.workflow.workflow_operations.file_exists")
    @patch("src.workflow.workflow_operations.get_workflows_directory")
    def test_delete_workflow_not_found(self, mock_get_dir, mock_file_exists):
        """测试删除不存在的工作流"""
        mock_get_dir.return_value = "/fake/workflows/dir"
        mock_file_exists.return_value = False
        # Mock os.listdir to return an empty list since we're testing the file not found case
        with patch("src.workflow.workflow_operations.os.listdir", return_value=[]):
            result = delete_workflow("nonexistent")

            self.assertFalse(result)
            mock_file_exists.assert_called_once_with("/fake/workflows/dir/nonexistent.json")


if __name__ == "__main__":
    unittest.main()
