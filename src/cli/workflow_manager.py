#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流管理命令行工具

提供创建、查看、执行工作流等功能，以及与n8n的同步操作。
"""

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.adapters.n8n_adapter import N8nAdapter
from src.adapters.status_sync_adapter import StatusSyncAdapter
from src.db.models.workflow import Workflow, WorkflowExecution, WorkflowStep
from src.db.repositories.workflow_repository import (
    WorkflowExecutionRepository,
    WorkflowRepository,
    WorkflowStepRepository,
)
from src.db.session import SessionLocal

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def get_session() -> Session:
    """获取数据库会话

    Returns:
        SQLAlchemy会话对象
    """
    return SessionLocal()


def list_workflows(args: argparse.Namespace) -> None:
    """列出所有工作流

    Args:
        args: 命令行参数
    """
    session = get_session()
    try:
        repo = WorkflowRepository(session)
        workflows = repo.get_all()

        if not workflows:
            print("没有找到工作流")
            return

        print(f"找到 {len(workflows)} 个工作流:")
        for workflow in workflows:
            status_icon = "🟢" if workflow.status == "active" else "⚪️"
            n8n_id = f"(n8n ID: {workflow.n8n_workflow_id})" if workflow.n8n_workflow_id else ""
            print(f"{status_icon} {workflow.id}: {workflow.name} {n8n_id}")
            if args.verbose:
                print(f"  描述: {workflow.description or '无'}")
                print(f"  创建时间: {workflow.created_at}")
                print(f"  更新时间: {workflow.updated_at}")
                print(f"  n8n URL: {workflow.n8n_workflow_url or '无'}")
                print()
    finally:
        session.close()


def view_workflow(args: argparse.Namespace) -> None:
    """查看工作流详情

    Args:
        args: 命令行参数
    """
    session = get_session()
    try:
        repo = WorkflowRepository(session)
        step_repo = WorkflowStepRepository(session)
        execution_repo = WorkflowExecutionRepository(session)

        workflow = repo.get_by_id(args.id)
        if not workflow:
            print(f"工作流不存在: {args.id}")
            return

        # 显示工作流基本信息
        status_icon = "🟢" if workflow.status == "active" else "⚪️"
        print(f"{status_icon} {workflow.name} (ID: {workflow.id})")
        print(f"描述: {workflow.description or '无'}")
        print(f"状态: {workflow.status}")
        print(f"创建时间: {workflow.created_at}")
        print(f"更新时间: {workflow.updated_at}")
        print(f"n8n工作流ID: {workflow.n8n_workflow_id or '无'}")
        print(f"n8n工作流URL: {workflow.n8n_workflow_url or '无'}")

        # 显示工作流步骤
        steps = step_repo.get_by_workflow(workflow.id)
        if steps:
            print("\n步骤:")
            for step in steps:
                print(f"  {step.order + 1}. {step.name} ({step.step_type})")
                if args.verbose:
                    print(f"     描述: {step.description or '无'}")
                    if step.config:
                        print(f"     配置: {json.dumps(step.config, ensure_ascii=False, indent=2)}")
        else:
            print("\n没有定义步骤")

        # 显示最近的执行记录
        executions = execution_repo.get_by_workflow(workflow.id)
        if executions:
            print("\n最近的执行记录:")
            for execution in executions[:5]:  # 只显示最近5条
                status_map = {
                    "pending": "⏳",
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "cancelled": "⛔",
                }
                status_icon = status_map.get(execution.status.lower(), "❓")
                print(f"  {status_icon} {execution.id} - {execution.status}")
                print(f"     开始时间: {execution.started_at}")
                if execution.completed_at:
                    print(f"     完成时间: {execution.completed_at}")
                if execution.n8n_execution_id:
                    print(f"     n8n执行ID: {execution.n8n_execution_id}")
                if args.verbose and execution.error:
                    print(f"     错误: {execution.error}")
                print()
        else:
            print("\n没有执行记录")
    finally:
        session.close()


def create_workflow(args: argparse.Namespace) -> None:
    """创建工作流

    Args:
        args: 命令行参数
    """
    session = get_session()
    try:
        repo = WorkflowRepository(session)

        # 创建工作流
        workflow_id = str(uuid.uuid4())
        workflow_data = {
            "id": workflow_id,
            "name": args.name,
            "description": args.description,
            "status": "active" if args.active else "inactive",
        }

        workflow = repo.create(workflow_data)
        print(f"成功创建工作流: {workflow.name} (ID: {workflow.id})")

        # 如果指定了n8n工作流ID，则关联
        if args.n8n_id:
            n8n_adapter = N8nAdapter()
            n8n_workflow = n8n_adapter.get_workflow(args.n8n_id)
            if n8n_workflow:
                workflow.n8n_workflow_id = args.n8n_id
                workflow.n8n_workflow_url = f"{n8n_adapter.base_url}/workflow/{args.n8n_id}"
                session.commit()
                print(f"成功关联n8n工作流: {args.n8n_id}")
            else:
                print(f"警告: 未找到n8n工作流 {args.n8n_id}")
    finally:
        session.close()


def update_workflow(args: argparse.Namespace) -> None:
    """更新工作流

    Args:
        args: 命令行参数
    """
    session = get_session()
    try:
        repo = WorkflowRepository(session)
        workflow = repo.get_by_id(args.id)
        if not workflow:
            print(f"工作流不存在: {args.id}")
            return

        # 准备更新数据
        update_data = {}
        if args.name is not None:
            update_data["name"] = args.name
        if args.description is not None:
            update_data["description"] = args.description
        if args.status is not None:
            update_data["status"] = args.status

        # 更新工作流
        if update_data:
            workflow = repo.update(args.id, update_data)
            print(f"成功更新工作流: {workflow.name} (ID: {workflow.id})")
        else:
            print("没有提供更新数据")

        # 如果指定了n8n工作流ID，则关联
        if args.n8n_id:
            n8n_adapter = N8nAdapter()
            n8n_workflow = n8n_adapter.get_workflow(args.n8n_id)
            if n8n_workflow:
                workflow.n8n_workflow_id = args.n8n_id
                workflow.n8n_workflow_url = f"{n8n_adapter.base_url}/workflow/{args.n8n_id}"
                session.commit()
                print(f"成功关联n8n工作流: {args.n8n_id}")
            else:
                print(f"警告: 未找到n8n工作流 {args.n8n_id}")
    finally:
        session.close()


def delete_workflow(args: argparse.Namespace) -> None:
    """删除工作流

    Args:
        args: 命令行参数
    """
    session = get_session()
    try:
        repo = WorkflowRepository(session)
        workflow = repo.get_by_id(args.id)
        if not workflow:
            print(f"工作流不存在: {args.id}")
            return

        # 确认删除
        if not args.force:
            confirm = input(f"确定要删除工作流 '{workflow.name}' (ID: {workflow.id})? [y/N] ")
            if confirm.lower() != "y":
                print("已取消删除")
                return

        # 删除工作流
        repo.delete(args.id)
        print(f"成功删除工作流: {workflow.name} (ID: {workflow.id})")
    finally:
        session.close()


def execute_workflow(args: argparse.Namespace) -> None:
    """执行工作流

    Args:
        args: 命令行参数
    """
    session = get_session()
    try:
        workflow_repo = WorkflowRepository(session)
        execution_repo = WorkflowExecutionRepository(session)

        workflow = workflow_repo.get_by_id(args.id)
        if not workflow:
            print(f"工作流不存在: {args.id}")
            return

        # 创建执行记录
        execution_id = str(uuid.uuid4())
        context = {}
        if args.context:
            try:
                context = json.loads(args.context)
            except json.JSONDecodeError:
                print("错误: 上下文必须是有效的JSON格式")
                return

        execution_data = {
            "id": execution_id,
            "workflow_id": workflow.id,
            "status": "pending",
            "context": context,
        }

        execution = execution_repo.create(execution_data)
        print(f"成功创建执行记录: {execution.id}")

        # 如果工作流关联了n8n工作流，则触发n8n工作流
        if workflow.n8n_workflow_id:
            n8n_adapter = N8nAdapter()
            payload = {
                "execution_id": execution.id,
                "workflow_id": workflow.id,
                "context": context,
            }
            result = n8n_adapter.trigger_workflow(workflow.n8n_workflow_id, payload)
            if result:
                # 更新n8n执行ID
                execution.n8n_execution_id = result.get("id")
                execution.status = "running"
                session.commit()
                print(f"成功触发n8n工作流: {workflow.n8n_workflow_id}, 执行ID: {result.get('id')}")
            else:
                print(f"触发n8n工作流失败: {workflow.n8n_workflow_id}")
                execution.status = "failed"
                execution.error = "触发n8n工作流失败"
                session.commit()
        else:
            print("警告: 此工作流未关联n8n工作流，无法自动执行")
    finally:
        session.close()


def sync_n8n(args: argparse.Namespace) -> None:
    """同步n8n工作流

    Args:
        args: 命令行参数
    """
    session = get_session()
    try:
        adapter = StatusSyncAdapter(session)

        if args.import_workflows:
            count = adapter.import_n8n_workflows()
            print(f"成功导入 {count} 个n8n工作流")
        elif args.workflow_id:
            if args.execution_id:
                # 同步特定执行状态
                success = adapter.sync_execution_status(args.execution_id)
                print(f"同步执行状态 {'成功' if success else '失败'}: {args.execution_id}")
            else:
                # 同步工作流状态
                success = adapter.sync_workflow_status(args.workflow_id)
                print(f"同步工作流状态 {'成功' if success else '失败'}: {args.workflow_id}")
        elif args.update_from_n8n and args.n8n_execution_id:
            # 从n8n更新执行状态
            success = adapter.update_execution_from_n8n(args.n8n_execution_id)
            print(f"从n8n更新执行状态 {'成功' if success else '失败'}: {args.n8n_execution_id}")
        elif args.sync_pending:
            # 同步所有待处理的执行
            count = adapter.sync_pending_executions()
            print(f"成功同步 {count} 个待处理执行")
        else:
            print("错误: 请指定同步操作")
    finally:
        session.close()


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
    update_parser.add_argument("-s", "--status", choices=["active", "inactive", "archived"], help="工作流状态")
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
