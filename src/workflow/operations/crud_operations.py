#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流CRUD操作模块

提供创建、更新和删除工作流的功能
"""

import argparse
import logging
import uuid
from typing import Any, Dict

from adapters.n8n import N8nAdapter
from src.db.repositories.workflow_repository import WorkflowRepository
from src.workflow.workflow_utils import get_session

logger = logging.getLogger(__name__)


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
