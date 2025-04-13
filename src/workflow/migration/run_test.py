#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模型测试入口点脚本

提供命令行接口运行数据库模型测试。
"""

import argparse
import logging
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.workflow.migration.test_models import test_create_workflow_with_stages_and_transitions

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行工作流模型测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("开始运行工作流模型测试...")

    try:
        success = test_create_workflow_with_stages_and_transitions()
        if success:
            logger.info("✅ 测试成功完成!")
            return 0
        else:
            logger.error("❌ 测试失败!")
            return 1
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {str(e)}")
        if args.verbose:
            import traceback

            logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
