#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流列表操作模块

提供列出和查看工作流的功能
"""

import argparse
import json
import logging
from typing import Any, Dict

from src.db.repositories.workflow_repository import (
    WorkflowExecutionRepository,
    WorkflowRepository,
    WorkflowStepRepository,
)
from src.workflow.workflow_utils import get_session

logger = logging.getLogger(__name__)


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
        _display_workflow_executions(execution_repo, workflow.id, args.verbose)
    finally:
        session.close()


def _display_workflow_executions(execution_repo, workflow_id, verbose=False):
    """显示工作流执行记录

    Args:
        execution_repo: 执行记录仓库
        workflow_id: 工作流ID
        verbose: 是否显示详细信息
    """
    executions = execution_repo.get_by_workflow(workflow_id)
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
            if verbose and execution.error:
                print(f"     错误: {execution.error}")
            print()
