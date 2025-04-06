#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流管理命令行工具

提供创建、查看、执行工作流等功能，以及与n8n的同步操作。
"""

import argparse
import logging
import sys
from typing import Any, Dict, List, Optional

from src.workflow.workflow_operations import (
    create_workflow,
    delete_workflow,
    execute_workflow,
    list_workflows,
    sync_n8n,
    update_workflow,
    view_workflow,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="工作流管理工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # list命令
    list_parser = subparsers.add_parser("list", help="列出所有工作流")
    list_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    list_parser.set_defaults(func=list_workflows)

    # view命令
    view_parser = subparsers.add_parser("view", help="查看工作流详情")
    view_parser.add_argument("id", help="工作流ID")
    view_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    view_parser.set_defaults(func=view_workflow)

    # create命令
    create_parser = subparsers.add_parser("create", help="创建工作流")
    create_parser.add_argument("name", help="工作流名称")
    create_parser.add_argument("-d", "--description", help="工作流描述")
    create_parser.add_argument("--active", action="store_true", help="设置为活跃状态")
    create_parser.add_argument("--n8n-id", help="关联的n8n工作流ID")
    create_parser.set_defaults(func=create_workflow)

    # update命令
    update_parser = subparsers.add_parser("update", help="更新工作流")
    update_parser.add_argument("id", help="工作流ID")
    update_parser.add_argument("-n", "--name", help="工作流名称")
    update_parser.add_argument("-d", "--description", help="工作流描述")
    update_parser.add_argument(
        "-s", "--status", choices=["active", "inactive", "archived"], help="工作流状态"
    )
    update_parser.add_argument("--n8n-id", help="关联的n8n工作流ID")
    update_parser.set_defaults(func=update_workflow)

    # delete命令
    delete_parser = subparsers.add_parser("delete", help="删除工作流")
    delete_parser.add_argument("id", help="工作流ID")
    delete_parser.add_argument("-f", "--force", action="store_true", help="强制删除，不确认")
    delete_parser.set_defaults(func=delete_workflow)

    # execute命令
    execute_parser = subparsers.add_parser("execute", help="执行工作流")
    execute_parser.add_argument("id", help="工作流ID")
    execute_parser.add_argument("-c", "--context", help="执行上下文，JSON格式")
    execute_parser.set_defaults(func=execute_workflow)

    # sync命令
    sync_parser = subparsers.add_parser("sync", help="同步n8n工作流")
    sync_parser.add_argument("-w", "--workflow-id", help="工作流ID")
    sync_parser.add_argument("-e", "--execution-id", help="执行ID")
    sync_parser.add_argument("-n", "--n8n-execution-id", help="n8n执行ID")
    sync_parser.add_argument("--import-workflows", action="store_true", help="导入n8n工作流")
    sync_parser.add_argument("--update-from-n8n", action="store_true", help="从n8n更新执行状态")
    sync_parser.add_argument("--sync-pending", action="store_true", help="同步所有待处理的执行")
    sync_parser.set_defaults(func=sync_n8n)

    # 解析命令行参数
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
