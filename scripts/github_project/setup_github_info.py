#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub信息设置脚本

此脚本已过时 - 请改用 'vc status init' 命令配置GitHub信息
"""

import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """主函数 - 提示使用新命令代替此脚本"""
    logger.warning("此脚本已过时。请改用 'vc status init' 命令配置GitHub信息。")
    logger.info("执行以下命令配置GitHub信息:")
    logger.info("    vc status init")

    # 显示当前的GitHub信息配置
    try:
        from src.status.service import StatusService

        status_service = StatusService.get_instance()
        github_info = status_service.get_domain_status("github_info")

        if github_info and "github_info" in github_info:
            data = github_info["github_info"]
            logger.info("当前GitHub配置:")
            logger.info(f"  所有者: {data.get('effective_owner') or '未设置'}")
            logger.info(f"  仓库: {data.get('effective_repo') or '未设置'}")
            logger.info(f"  项目ID: {data.get('effective_project_id') or '未设置'}")
            logger.info(f"  标题: {data.get('roadmap_title') or '未设置'}")
            source = data.get("source", "unknown")
            logger.info(f"  配置来源: {source}")
        else:
            logger.info("当前未配置GitHub信息")
    except Exception as e:
        logger.error(f"获取当前GitHub配置时出错: {e}")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
