#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工作流高级操作功能
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

# 更新导入路径
from src.workflow.analytics.workflow_analytics import _analyze_workflow_progress, calculate_progress_statistics, get_workflow_executions
from src.workflow.operations import list_workflows


class TestWorkflowAdvancedOperations(unittest.TestCase):
    """测试工作流高级操作功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.executions_dir = os.path.join(self.temp_dir, "executions")
        os.makedirs(self.executions_dir, exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    # 删除测试已移除函数的用例
    # def test_execute_workflow(self):
    # def test_execute_workflow_not_found(self):
    # def test_execute_script_step(self):
    # def test_execute_api_call_step(self):
    # def test_execute_condition_step(self):
    # def test_execute_unknown_step_type(self):
    # def test_save_execution_result(self):

    @patch("src.workflow.analytics.workflow_analytics.get_config")
    @patch("src.workflow.analytics.workflow_analytics.os.path.exists")
    @patch("src.workflow.analytics.workflow_analytics.os.listdir")
    def test_get_workflow_executions(self, mock_listdir, mock_exists, mock_get_config):
        """测试获取工作流执行历史"""
        mock_get_config.return_value = {"paths": {"data_dir": self.temp_dir}}
        mock_exists.return_value = True

        # 创建执行历史文件
        executions_dir = os.path.join(self.temp_dir, "workflow_executions")
        os.makedirs(executions_dir, exist_ok=True)

        exec1 = {"id": "exec1", "start_time": "2023-01-01T12:00:00", "success": True}
        exec2 = {"id": "exec2", "start_time": "2023-01-01T13:00:00", "success": False}

        # 使用工作流ID前缀的文件名
        with open(os.path.join(executions_dir, "test-workflow_20230101120000.json"), "w") as f:
            json.dump(exec1, f)
        with open(os.path.join(executions_dir, "test-workflow_20230101130000.json"), "w") as f:
            json.dump(exec2, f)

        mock_listdir.return_value = ["test-workflow_20230101120000.json", "test-workflow_20230101130000.json", "not_a_json.txt"]

        with patch("src.workflow.analytics.workflow_analytics.read_json_file") as mock_read_json:
            mock_read_json.side_effect = lambda path: exec1 if "120000" in path else exec2

            executions = get_workflow_executions("test-workflow")

            # 应该按照时间排序，最新的在前面
            self.assertEqual(len(executions), 2)
            self.assertEqual(executions[0], exec2)
            self.assertEqual(executions[1], exec1)

    @patch("src.workflow.analytics.workflow_analytics.list_workflows")
    @patch("src.workflow.analytics.workflow_analytics._analyze_workflow_progress")
    def test_calculate_progress_statistics_all(self, mock_analyze, mock_list_workflows):
        """测试计算所有工作流的进度统计"""
        workflows = [{"id": "wf1", "name": "Workflow 1"}, {"id": "wf2", "name": "Workflow 2"}]
        mock_list_workflows.return_value = workflows

        # 定义工作流统计数据的结构，对应_analyze_workflow_progress的返回值
        wf1_stats = {
            "id": "wf1",
            "name": "Workflow 1",
            "total_steps": 3,
            "execution_count": 5,
            "last_execution": {"time": "2023-01-01T12:00:00", "status": "completed"},
            "status": "completed",
        }
        wf2_stats = {
            "id": "wf2",
            "name": "Workflow 2",
            "total_steps": 2,
            "execution_count": 3,
            "last_execution": {"time": "2023-01-01T13:00:00", "status": "in_progress"},
            "status": "in_progress",
        }
        mock_analyze.side_effect = [wf1_stats, wf2_stats]

        stats = calculate_progress_statistics()

        # 验证结果包含正确的总体统计数据
        self.assertEqual(stats["total_workflows"], 2)
        self.assertEqual(stats["completed_workflows"], 1)
        self.assertEqual(stats["in_progress_workflows"], 1)
        self.assertEqual(stats["not_started_workflows"], 0)

        # 验证工作流详情数据
        self.assertEqual(len(stats["workflows_details"]), 2)
        self.assertEqual(stats["workflows_details"][0], wf1_stats)
        self.assertEqual(stats["workflows_details"][1], wf2_stats)
        self.assertEqual(mock_analyze.call_count, 2)

    @patch("src.workflow.analytics.workflow_analytics.get_workflow")
    @patch("src.workflow.analytics.workflow_analytics._analyze_workflow_progress")
    def test_calculate_progress_statistics_single(self, mock_analyze, mock_get_workflow):
        """测试计算单个工作流的进度统计"""
        workflow = {"id": "wf1", "name": "Workflow 1"}
        mock_get_workflow.return_value = workflow

        wf_stats = {
            "id": "wf1",
            "name": "Workflow 1",
            "total_steps": 3,
            "execution_count": 5,
            "last_execution": {"time": "2023-01-01T12:00:00", "status": "completed"},
            "status": "completed",
        }
        mock_analyze.return_value = wf_stats

        stats = calculate_progress_statistics("wf1")

        # 验证结果包含正确的总体统计数据
        self.assertEqual(stats["total_workflows"], 1)
        self.assertEqual(stats["completed_workflows"], 1)
        self.assertEqual(stats["in_progress_workflows"], 0)
        self.assertEqual(stats["not_started_workflows"], 0)

        # 验证工作流详情数据
        self.assertEqual(len(stats["workflows_details"]), 1)
        self.assertEqual(stats["workflows_details"][0], wf_stats)
        mock_get_workflow.assert_called_once_with("wf1")
        mock_analyze.assert_called_once_with(workflow)

    @patch("src.workflow.analytics.workflow_analytics.get_workflow_executions")
    def test_analyze_workflow_progress(self, mock_get_executions):
        """测试分析工作流进度"""
        workflow = {"id": "test-workflow", "name": "Test Workflow", "steps": [{"id": "step1"}, {"id": "step2"}]}

        executions = [{"start_time": "2023-01-01T12:00:00", "status": "completed"}, {"start_time": "2023-01-01T11:00:00", "status": "error"}]
        mock_get_executions.return_value = executions

        result = _analyze_workflow_progress(workflow)

        self.assertEqual(result["id"], "test-workflow")
        self.assertEqual(result["name"], "Test Workflow")
        self.assertEqual(result["total_steps"], 2)
        self.assertEqual(result["execution_count"], 2)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["last_execution"]["time"], "2023-01-01T12:00:00")
        self.assertEqual(result["last_execution"]["status"], "completed")

    @patch("src.workflow.analytics.workflow_analytics.get_workflow_executions")
    def test_analyze_workflow_progress_no_executions(self, mock_get_executions):
        """测试分析没有执行历史的工作流进度"""
        workflow = {"id": "test-workflow", "name": "Test Workflow", "steps": [{"id": "step1"}, {"id": "step2"}]}

        mock_get_executions.return_value = []

        result = _analyze_workflow_progress(workflow)

        self.assertEqual(result["id"], "test-workflow")
        self.assertEqual(result["name"], "Test Workflow")
        self.assertEqual(result["total_steps"], 2)
        self.assertEqual(result["execution_count"], 0)
        self.assertEqual(result["status"], "not_started")
        self.assertIsNone(result["last_execution"])


if __name__ == "__main__":
    unittest.main()
