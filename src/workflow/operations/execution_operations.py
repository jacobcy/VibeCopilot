#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行操作模块

提供执行工作流和同步n8n的功能
"""

import argparse
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from adapters.n8n import N8nAdapter
from adapters.status_sync import StatusSyncAdapter
from src.db.repositories.workflow_repository import (
    WorkflowExecutionRepository,
    WorkflowRepository,
    WorkflowStepRepository,
)
from src.workflow.workflow_utils import get_session

logger = logging.getLogger(__name__)


def execute_workflow(args: argparse.Namespace) -> None:
    """执行工作流

    Args:
        args: 命令行参数
    """
    session = get_session()
    try:
        repo = WorkflowRepository(session)
        execution_repo = WorkflowExecutionRepository(session)
        step_repo = WorkflowStepRepository(session)

        workflow = repo.get_by_id(args.id)
        if not workflow:
            print(f"工作流不存在: {args.id}")
            return

        # 创建执行记录
        execution_id = str(uuid.uuid4())
        execution_data = {
            "id": execution_id,
            "workflow_id": workflow.id,
            "status": "pending",
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        execution = execution_repo.create(execution_data)
        print(f"已创建执行记录: {execution.id}")

        # 准备执行参数
        input_data = {}
        if args.input:
            try:
                input_data = json.loads(args.input)
            except json.JSONDecodeError:
                print("警告: 输入数据格式不正确，将使用空对象")

        # 如果有n8n工作流ID，则通过n8n执行
        if workflow.n8n_workflow_id:
            try:
                n8n_adapter = N8nAdapter()
                result = n8n_adapter.execute_workflow(workflow.n8n_workflow_id, input_data)

                if result and "executionId" in result:
                    # 更新执行记录
                    execution_repo.update(
                        execution.id,
                        {
                            "status": "running",
                            "n8n_execution_id": result["executionId"],
                        },
                    )
                    print(f"已提交到n8n执行: {result['executionId']}")

                    # 如果指定了等待
                    if args.wait:
                        print("等待工作流执行完成...")
                        wait_result = _wait_for_n8n_execution(
                            n8n_adapter, result["executionId"], args.timeout
                        )

                        if wait_result:
                            status = "completed" if wait_result.get("success", False) else "failed"
                            execution_repo.update(
                                execution.id,
                                {
                                    "status": status,
                                    "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "result": wait_result,
                                },
                            )
                            print(f"工作流执行{status}！")
                else:
                    # 执行失败
                    execution_repo.update(
                        execution.id,
                        {
                            "status": "failed",
                            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "error": "提交到n8n执行失败",
                        },
                    )
                    print("提交到n8n执行失败")
            except Exception as e:
                # 捕获异常
                execution_repo.update(
                    execution.id,
                    {
                        "status": "failed",
                        "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "error": str(e),
                    },
                )
                print(f"执行出错: {str(e)}")
        else:
            print("工作流未关联n8n工作流，本地执行功能开发中...")
            # 更新执行记录
            execution_repo.update(
                execution.id,
                {
                    "status": "failed",
                    "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "error": "工作流未关联n8n工作流",
                },
            )
    finally:
        session.close()


def _wait_for_n8n_execution(n8n_adapter, execution_id, timeout=60):
    """等待n8n工作流执行完成

    Args:
        n8n_adapter: n8n适配器
        execution_id: 执行ID
        timeout: 超时时间（秒）

    Returns:
        执行结果
    """
    start_time = time.time()
    while True:
        # 检查是否超时
        if time.time() - start_time > timeout:
            print(f"等待超时 ({timeout}秒)")
            return None

        # 获取执行状态
        execution = n8n_adapter.get_execution(execution_id)
        if not execution:
            print("无法获取执行状态")
            return None

        # 检查执行状态
        if execution.get("finished"):
            return execution

        # 等待一段时间
        time.sleep(2)


def sync_n8n(args: argparse.Namespace) -> None:
    """同步n8n工作流

    Args:
        args: 命令行参数
    """
    session = get_session()
    try:
        repo = WorkflowRepository(session)

        # 连接n8n
        n8n_adapter = N8nAdapter()
        n8n_workflows = n8n_adapter.get_all_workflows()

        if not n8n_workflows:
            print("未找到n8n工作流")
            return

        print(f"找到 {len(n8n_workflows)} 个n8n工作流")

        # 同步工作流
        count = 0
        for n8n_workflow in n8n_workflows:
            # 检查是否已存在
            existing = repo.find_by_n8n_id(n8n_workflow["id"])

            if existing:
                # 更新
                if args.update:
                    repo.update(
                        existing.id,
                        {
                            "name": n8n_workflow["name"],
                            "n8n_workflow_url": f"{n8n_adapter.base_url}/workflow/{n8n_workflow['id']}",
                        },
                    )
                    print(f"已更新工作流: {n8n_workflow['name']}")
                    count += 1
            else:
                # 创建新工作流
                if args.create:
                    workflow_id = str(uuid.uuid4())
                    workflow_data = {
                        "id": workflow_id,
                        "name": n8n_workflow["name"],
                        "description": f"从n8n同步的工作流",
                        "status": "active",
                        "n8n_workflow_id": n8n_workflow["id"],
                        "n8n_workflow_url": f"{n8n_adapter.base_url}/workflow/{n8n_workflow['id']}",
                    }

                    repo.create(workflow_data)
                    print(f"已创建工作流: {n8n_workflow['name']}")
                    count += 1

        print(f"同步完成，处理了 {count} 个工作流")

        # 同步实时状态
        if args.status:
            print("同步实时状态...")
            status_adapter = StatusSyncAdapter()
            status_adapter.sync_all_status()
            print("状态同步完成")

    finally:
        session.close()
