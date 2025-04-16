#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VibeCopilot Memory和Sync责任分离测试

测试Memory系统与同步系统的责任是否正确分离：
1. Memory系统只提供存储接口，不参与同步决策
2. SyncExecutor专注于执行存储操作
3. 保证接口稳定性和系统模块化
"""

import inspect
import logging
import unittest
from unittest.mock import MagicMock, patch

from src.memory import get_memory_service
from src.memory.sync_executor import SyncExecutor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncSeparationTest(unittest.TestCase):
    """测试Memory系统和同步系统的责任分离"""

    def setUp(self):
        """测试前准备工作"""
        self.memory_service = get_memory_service()

    def test_memory_service_interface(self):
        """测试MemoryService是否只提供同步接口而不执行同步逻辑"""
        # 1. 检查MemoryService.sync_all方法是否存在
        self.assertTrue(hasattr(self.memory_service, "sync_all"), "MemoryService缺少sync_all方法")

        # 2. 验证sync_all方法返回接口就绪状态而非执行实际同步
        success, message, data = self.memory_service.sync_all()
        self.assertTrue(success, f"sync_all方法返回失败: {message}")

        # 确保返回的是接口就绪信息，表明它不执行实际同步操作
        # 而是等待外部系统调用execute_storage方法
        self.assertIn("status", data, "sync_all返回的数据缺少status字段")
        self.assertEqual(data.get("status"), "ready", f"sync_all应只返回接口就绪状态，但返回了: {data.get('status')}")

    def test_execute_storage_method(self):
        """测试MemoryService提供execute_storage方法供外部系统调用"""
        # 检查MemoryService.execute_storage方法是否存在
        self.assertTrue(hasattr(self.memory_service, "execute_storage"), "MemoryService缺少execute_storage方法")

        # 检查execute_storage方法签名
        sig = inspect.signature(self.memory_service.execute_storage)
        params = sig.parameters

        # 验证参数列表符合接口规范
        expected_params = ["texts", "metadata_list", "collection_name"]
        for param in expected_params:
            self.assertIn(param, params, f"execute_storage方法缺少必要参数: {param}")

    def test_sync_executor_responsibility(self):
        """测试SyncExecutor是否专注于执行存储操作而不参与同步决策"""
        # 创建SyncExecutor实例
        executor = SyncExecutor()

        # 检查SyncExecutor必须实现execute_storage方法
        self.assertTrue(hasattr(executor, "execute_storage"), "SyncExecutor缺少execute_storage方法")

        # 检查SyncExecutor是否不包含与同步决策相关的方法
        decision_related_methods = ["decide_sync_files", "collect_sync_files", "scan_directory", "watch_filesystem"]

        for method in decision_related_methods:
            self.assertFalse(hasattr(executor, method), f"SyncExecutor不应包含同步决策相关方法: {method}")

    @patch("src.memory.sync_executor.BasicMemoryAdapter")
    def test_sync_executor_forward_calls(self, mock_adapter):
        """测试SyncExecutor正确转发调用到向量存储适配器"""
        # 创建Mock对象
        mock_instance = MagicMock()
        mock_adapter.return_value = mock_instance
        mock_instance.store.return_value = ["memory://test/doc1", "memory://test/doc2"]

        # 测试数据
        texts = ["文本1", "文本2"]
        metadata = [{"title": "文档1"}, {"title": "文档2"}]
        collection = "测试集合"

        # 创建执行器并调用方法
        executor = SyncExecutor()
        import asyncio

        # 使用同步方式调用异步方法（仅用于测试）
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(executor.execute_storage(texts, metadata, collection))

        # 验证调用
        mock_instance.store.assert_called_once_with(texts, metadata, collection)

        # 验证返回值
        self.assertEqual(len(result), 2, "应返回两个permalink")
        self.assertTrue(all(p.startswith("memory://") for p in result), "返回的所有项应为permalink格式")


class ModularSeparationTest(unittest.TestCase):
    """测试模块化分离和接口稳定性"""

    def test_memory_service_isolation(self):
        """测试MemoryService是否充分隔离，不依赖同步系统具体实现"""
        # 检查MemoryService的import项不应直接依赖于同步系统组件
        import importlib
        import inspect

        try:
            # 获取MemoryService实现类的源码
            from src.memory.services import MemoryServiceImpl

            source = inspect.getsource(MemoryServiceImpl)

            # 检查不应导入与同步决策相关的模块
            forbidden_imports = ["from src.sync import", "import src.sync", "from src.sync.", "SyncOrchestrator"]

            for forbidden in forbidden_imports:
                self.assertNotIn(forbidden, source, f"MemoryService实现不应导入同步系统组件: {forbidden}")

            # 验证MemoryService不应依赖同步系统类型
            # 注意：可能存在误报，因为简单的字符串搜索可能不够准确
            sync_system_types = ["FileScanner", "SyncOrchestrator", "FileWatcher", "SyncManager"]

            for type_name in sync_system_types:
                self.assertNotIn(f"def __init__(self, {type_name}", source, f"MemoryService不应在初始化时依赖同步系统类型: {type_name}")

        except ImportError:
            logger.warning("无法导入MemoryServiceImpl进行源码分析")
            self.skipTest("无法导入MemoryServiceImpl")


def run_separation_tests():
    """运行所有责任分离测试"""
    sync_suite = unittest.TestLoader().loadTestsFromTestCase(SyncSeparationTest)
    modular_suite = unittest.TestLoader().loadTestsFromTestCase(ModularSeparationTest)

    # 创建测试套件
    all_tests = unittest.TestSuite([sync_suite, modular_suite])

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    results = runner.run(all_tests)

    return results.wasSuccessful()


if __name__ == "__main__":
    logging.info("=== VibeCopilot Memory和Sync责任分离测试开始 ===")

    if run_separation_tests():
        print("\n✅ 责任分离测试通过")
        exit(0)
    else:
        print("\n❌ 责任分离测试失败")
        exit(1)
