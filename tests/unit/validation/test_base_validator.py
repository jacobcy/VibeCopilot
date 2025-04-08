"""
测试基础验证器模块

测试内容：
- ValidationResult类的功能
- BaseValidator子类功能
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from src.validation.core.base_validator import BaseValidator, ValidationResult


class TestValidationResult(unittest.TestCase):
    """测试ValidationResult类"""

    def test_init(self):
        """测试初始化"""
        # 默认值测试
        result = ValidationResult(True)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.data, {})
        self.assertEqual(result.messages, [])

        # 传入参数测试
        result = ValidationResult(False, {"key": "value"}, ["error"])
        self.assertFalse(result.is_valid)
        self.assertEqual(result.data, {"key": "value"})
        self.assertEqual(result.messages, ["error"])

    def test_add_message(self):
        """测试添加消息"""
        result = ValidationResult(True)

        # 添加单个消息
        result.add_message("error1")
        self.assertEqual(result.messages, ["error1"])

        # 添加重复消息
        result.add_message("error1")
        self.assertEqual(result.messages, ["error1"])

        # 添加新消息
        result.add_message("error2")
        self.assertEqual(result.messages, ["error1", "error2"])

        # 添加空消息
        result.add_message("")
        self.assertEqual(result.messages, ["error1", "error2"])

        # 添加None
        result.add_message(None)
        self.assertEqual(result.messages, ["error1", "error2"])

    def test_add_messages(self):
        """测试添加多个消息"""
        result = ValidationResult(True)

        # 添加多个消息
        result.add_messages(["error1", "error2"])
        self.assertEqual(result.messages, ["error1", "error2"])

        # 添加重复消息
        result.add_messages(["error2", "error3"])
        self.assertEqual(result.messages, ["error1", "error2", "error3"])

        # 添加空列表
        result.add_messages([])
        self.assertEqual(result.messages, ["error1", "error2", "error3"])

        # 添加None
        result.add_messages(None)
        self.assertEqual(result.messages, ["error1", "error2", "error3"])

    def test_merge(self):
        """测试合并验证结果"""
        # 创建两个验证结果
        result1 = ValidationResult(True, {"key1": "value1"}, ["message1"])
        result2 = ValidationResult(True, {"key2": "value2"}, ["message2"])

        # 合并验证结果
        result1.merge(result2)
        self.assertTrue(result1.is_valid)
        self.assertEqual(result1.data, {"key1": "value1", "key2": "value2"})
        self.assertEqual(result1.messages, ["message1", "message2"])

        # 测试合并失败结果
        result3 = ValidationResult(False, {"key3": "value3"}, ["message3"])
        result1.merge(result3)
        self.assertFalse(result1.is_valid)
        self.assertEqual(result1.data, {"key1": "value1", "key2": "value2", "key3": "value3"})
        self.assertEqual(result1.messages, ["message1", "message2", "message3"])

        # 测试数据覆盖
        result4 = ValidationResult(True, {"key1": "new_value"}, ["message4"])
        result1.merge(result4)
        self.assertFalse(result1.is_valid)  # 保持之前的状态
        self.assertEqual(result1.data, {"key1": "new_value", "key2": "value2", "key3": "value3"})
        self.assertEqual(result1.messages, ["message1", "message2", "message3", "message4"])


class TestBaseValidator(unittest.TestCase):
    """测试BaseValidator抽象基类"""

    def setUp(self):
        """设置测试环境"""

        # 创建一个继承BaseValidator的测试类
        class TestValidator(BaseValidator):
            def validate(self, data):
                if data == "invalid":
                    return ValidationResult(False, messages=["Invalid data"])
                return ValidationResult(True, {"validated": data})

            def _load_from_file(self, file_path):
                with open(file_path, "r") as f:
                    return f.read().strip()

        self.validator_class = TestValidator
        self.validator = TestValidator({"test_config": "value"})

    def test_init(self):
        """测试初始化"""
        # 测试配置传入
        self.assertEqual(self.validator.config, {"test_config": "value"})

        # 测试默认配置
        validator = self.validator_class()
        self.assertEqual(validator.config, {})

    def test_validate(self):
        """测试验证方法"""
        # 测试有效数据
        result = self.validator.validate("valid")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.data, {"validated": "valid"})
        self.assertEqual(result.messages, [])

        # 测试无效数据
        result = self.validator.validate("invalid")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.data, {})
        self.assertEqual(result.messages, ["Invalid data"])

    def test_validate_from_file(self):
        """测试从文件验证"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp:
            tmp.write("valid")
            tmp_path = tmp.name

        try:
            # 测试有效文件
            result = self.validator.validate_from_file(tmp_path)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.data, {"validated": "valid"})

            # 测试文件不存在的情况
            non_existent_path = tmp_path + "_nonexistent"
            result = self.validator.validate_from_file(non_existent_path)
            self.assertFalse(result.is_valid)
            self.assertTrue(any("验证文件失败" in msg for msg in result.messages))

        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch("logging.getLogger")
    def test_logging(self, mock_get_logger):
        """测试日志记录"""
        # 设置模拟的logger
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # 创建验证器并故意引发异常
        validator = self.validator_class()

        # 模拟_load_from_file方法引发异常
        with patch.object(validator, "_load_from_file", side_effect=Exception("Test error")):
            result = validator.validate_from_file("test_path")

        # 验证结果
        self.assertFalse(result.is_valid)
        self.assertEqual(result.data, {})
        self.assertTrue(any("Test error" in msg for msg in result.messages))

        # 验证日志调用
        mock_logger.error.assert_called_once()
        self.assertTrue("test_path" in mock_logger.error.call_args[0][0])
        self.assertTrue("Test error" in mock_logger.error.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
