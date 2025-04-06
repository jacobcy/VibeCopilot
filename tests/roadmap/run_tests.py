#!/usr/bin/env python
"""
路线图测试运行脚本

运行路线图模块的所有单元测试和集成测试。
"""

import os
import sys
import unittest

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 导入测试模块
from tests.roadmap.test_basic import TestBasicImports
from tests.roadmap.test_service_refactor import TestRoadmapServiceRefactor


def run_tests():
    """
    运行路线图模块的所有测试

    Returns:
        unittest.TestResult: 测试结果
    """
    # 创建测试加载器
    loader = unittest.TestLoader()

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加基本测试
    try:
        suite.addTest(loader.loadTestsFromTestCase(TestBasicImports))
    except ImportError as e:
        print(f"警告: 无法导入基本测试: {e}")

    # 添加服务重构测试
    try:
        suite.addTest(loader.loadTestsFromTestCase(TestRoadmapServiceRefactor))
    except ImportError as e:
        print(f"警告: 无法导入服务重构测试: {e}")

    # 添加单元测试
    try:
        from tests.roadmap.test_manager import TestRoadmapManager
        from tests.roadmap.test_service import TestRoadmapService
        from tests.roadmap.test_status import TestRoadmapStatus

        suite.addTest(loader.loadTestsFromTestCase(TestRoadmapManager))
        suite.addTest(loader.loadTestsFromTestCase(TestRoadmapStatus))
        suite.addTest(loader.loadTestsFromTestCase(TestRoadmapService))
    except ImportError as e:
        print(f"警告: 无法导入单元测试: {e}")

    # 添加集成测试
    try:
        from tests.roadmap.test_integration import TestRoadmapIntegration

        suite.addTest(loader.loadTestsFromTestCase(TestRoadmapIntegration))
    except ImportError as e:
        print(f"警告: 无法导入集成测试: {e}")

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    print("=" * 70)
    print("开始运行路线图模块测试")
    print("=" * 70)

    # 运行测试
    result = run_tests()

    # 打印测试结果汇总
    print("\n" + "=" * 70)
    print(f"测试结果汇总:")
    print(f"运行测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print(f"跳过数: {len(result.skipped)}")
    print("=" * 70)

    # 根据测试结果设置退出码
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
