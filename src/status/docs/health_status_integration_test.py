#!/usr/bin/env python3
"""
Health和Status模块集成测试脚本

测试Health模块和Status模块的集成功能。
"""

import logging
import time
from typing import Any, Dict

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def init_modules():
    """初始化模块"""
    logger.info("初始化状态模块...")

    try:
        from src.status import initialize as init_status

        init_status()
        logger.info("状态模块初始化完成")
    except Exception as e:
        logger.error(f"状态模块初始化失败: {e}")
        raise


def test_health_check_results_publishing():
    """测试健康检查结果发布"""
    from src.health.checkers.base_checker import CheckResult
    from src.health.result_publisher import publish_health_check_result
    from src.status.service import get_domain_status

    logger.info("测试健康检查结果发布...")

    # 创建测试检查结果
    test_result = CheckResult(
        status="passed",
        details=["测试详情1", "测试详情2"],
        suggestions=["测试建议"],
        metrics={"test_metric": 100, "test_component": {"health": 90, "level": "good", "message": "测试组件状态"}},
    )

    # 发布结果
    success = publish_health_check_result("test_checker", test_result)

    if not success:
        logger.error("发布健康检查结果失败")
        raise Exception("发布健康检查结果失败")

    # 等待结果传播
    time.sleep(1)

    # 获取状态
    try:
        status_data = get_domain_status("health_check")
        logger.info(f"获取到状态数据: {status_data}")

        # 验证结果
        if status_data.get("status") != "passed":
            logger.error(f"状态不匹配: {status_data.get('status')} != passed")
            raise Exception("健康检查结果状态不匹配")

        logger.info("健康检查结果发布测试通过")
    except Exception as e:
        logger.error(f"获取状态数据失败: {e}")
        raise


def test_status_querying():
    """测试状态查询"""
    from src.health.status_api import get_status_health

    logger.info("测试状态查询API...")

    # 查询状态健康信息
    status_health = get_status_health()

    if "error" in status_health:
        logger.error(f"查询状态健康信息失败: {status_health['error']}")
        raise Exception(f"查询状态健康信息失败: {status_health['error']}")

    logger.info(f"获取到状态健康信息: {status_health}")
    logger.info("状态查询API测试通过")


def test_status_checker():
    """测试状态检查器"""
    from src.health.checkers.status_checker import StatusChecker

    logger.info("测试状态检查器...")

    # 创建检查器
    config = {
        "health_evaluation": {
            "min_overall_health": 65,
            "critical_domains": [{"domain": "task", "min_health": 70}, {"domain": "workflow", "min_health": 70}],
        },
        "api": {"timeout": 5, "retry_count": 2},
        "result_publishing": {"enabled": True},
    }

    checker = StatusChecker(config)

    # 执行检查
    result = checker.check()

    logger.info(f"状态检查结果: {result}")
    logger.info(f"状态: {result.status}")
    logger.info(f"详情: {result.details}")
    logger.info(f"建议: {result.suggestions}")
    logger.info(f"指标: {result.metrics}")

    logger.info("状态检查器测试通过")


def main():
    """主函数"""
    logger.info("开始Health和Status模块集成测试...")

    try:
        # 初始化模块
        init_modules()

        # 测试健康检查结果发布
        test_health_check_results_publishing()

        # 测试状态查询
        test_status_querying()

        # 测试状态检查器
        test_status_checker()

        logger.info("所有测试通过!")
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
