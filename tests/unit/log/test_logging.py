import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to sys.path to import the log_service module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log.log_service import (
    log_audit,
    log_error,
    log_operation_complete,
    log_operation_start,
    log_performance_metric,
    log_task_result,
    log_workflow_complete,
    log_workflow_start,
)


class TestLogService(unittest.TestCase):
    """
    测试日志服务各个功能的测试类
    """

    def setUp(self):
        """
        测试前准备工作，创建临时日志文件
        """
        self.test_workflow_id = "test-workflow-123"
        self.test_operation_id = "test-operation-456"
        self.test_user_id = "test-user-789"

    @patch("builtins.print")
    def test_workflow_logging(self, mock_print):
        """
        测试工作流日志功能
        """
        # 测试开始工作流日志
        log_workflow_start(workflow_id=self.test_workflow_id, workflow_name="Test Workflow", trigger_info={"source": "unit_test"})

        # 检查print被调用且包含预期的信息
        mock_print.assert_called()
        called_args = mock_print.call_args[0][0]
        self.assertIn(self.test_workflow_id, called_args)
        self.assertIn("Test Workflow", called_args)
        self.assertIn("unit_test", called_args)

        # 测试完成工作流日志
        log_workflow_complete(workflow_id=self.test_workflow_id, status="completed", result={"success": True})

        # 检查print被调用且包含预期的信息
        mock_print.assert_called()
        called_args = mock_print.call_args[0][0]
        self.assertIn(self.test_workflow_id, called_args)
        self.assertIn("completed", called_args)
        self.assertIn("success", called_args)

    @patch("builtins.print")
    def test_operation_logging(self, mock_print):
        """
        测试操作日志功能
        """
        # 测试开始操作日志
        log_operation_start(
            operation_id=self.test_operation_id, workflow_id=self.test_workflow_id, operation_name="Test Operation", parameters={"param1": "value1"}
        )

        # 检查print被调用且包含预期的信息
        mock_print.assert_called()
        called_args = mock_print.call_args[0][0]
        self.assertIn(self.test_operation_id, called_args)
        self.assertIn(self.test_workflow_id, called_args)
        self.assertIn("Test Operation", called_args)
        self.assertIn("param1", called_args)

        # 测试完成操作日志
        log_operation_complete(operation_id=self.test_operation_id, workflow_id=self.test_workflow_id, status="completed", result={"processed": 10})

        # 检查print被调用且包含预期的信息
        mock_print.assert_called()
        called_args = mock_print.call_args[0][0]
        self.assertIn(self.test_operation_id, called_args)
        self.assertIn(self.test_workflow_id, called_args)
        self.assertIn("completed", called_args)
        self.assertIn("processed", called_args)

    @patch("builtins.print")
    def test_task_result_logging(self, mock_print):
        """
        测试任务结果日志功能
        """
        log_task_result(
            task_id="test-task-001",
            operation_id=self.test_operation_id,
            workflow_id=self.test_workflow_id,
            task_name="Test Task",
            status="completed",
            result={"found": 5},
        )

        # 检查print被调用且包含预期的信息
        mock_print.assert_called()
        called_args = mock_print.call_args[0][0]
        self.assertIn("test-task-001", called_args)
        self.assertIn(self.test_operation_id, called_args)
        self.assertIn(self.test_workflow_id, called_args)
        self.assertIn("Test Task", called_args)
        self.assertIn("completed", called_args)
        self.assertIn("found", called_args)

    @patch("builtins.print")
    def test_performance_metric_logging(self, mock_print):
        """
        测试性能指标日志功能
        """
        log_performance_metric(
            metric_name="response_time",
            value=0.5,
            context={"endpoint": "/api/test"},
            workflow_id=self.test_workflow_id,
            operation_id=self.test_operation_id,
        )

        # 检查print被调用且包含预期的信息
        mock_print.assert_called()
        called_args = mock_print.call_args[0][0]
        self.assertIn("response_time", called_args)
        self.assertIn("0.5", called_args)
        self.assertIn("endpoint", called_args)
        self.assertIn(self.test_workflow_id, called_args)
        self.assertIn(self.test_operation_id, called_args)

    @patch("builtins.print")
    def test_error_logging(self, mock_print):
        """
        测试错误日志功能
        """
        log_error(
            error_message="Test error message",
            error_type="TestError",
            stack_trace="File test.py, line 10",
            workflow_id=self.test_workflow_id,
            operation_id=self.test_operation_id,
            context={"step": "testing"},
        )

        # 检查print被调用且包含预期的信息
        mock_print.assert_called()
        called_args = mock_print.call_args[0][0]
        self.assertIn("Test error message", called_args)
        self.assertIn("TestError", called_args)
        self.assertIn("File test.py", called_args)
        self.assertIn(self.test_workflow_id, called_args)
        self.assertIn(self.test_operation_id, called_args)
        self.assertIn("testing", called_args)

    @patch("builtins.print")
    def test_audit_logging(self, mock_print):
        """
        测试审计日志功能
        """
        log_audit(
            user_id=self.test_user_id,
            action="TEST_ACTION",
            resource_type="test_resource",
            resource_id="res-123",
            details={"reason": "testing"},
            workflow_id=self.test_workflow_id,
        )

        # 检查print被调用且包含预期的信息
        mock_print.assert_called()
        called_args = mock_print.call_args[0][0]
        self.assertIn(self.test_user_id, called_args)
        self.assertIn("TEST_ACTION", called_args)
        self.assertIn("test_resource", called_args)
        self.assertIn("res-123", called_args)
        self.assertIn("reason", called_args)
        self.assertIn(self.test_workflow_id, called_args)


if __name__ == "__main__":
    unittest.main()
