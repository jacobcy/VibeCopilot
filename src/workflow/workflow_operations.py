#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流操作模块 (基于flow_session实现)

提供兼容旧API的接口，内部使用新的flow_session实现。
"""

import argparse
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.db import get_engine, get_session_factory
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.db.repositories.stage_instance_repository import StageInstanceRepository
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
from src.flow_session import FlowSessionManager, FlowStatusIntegration, StageInstanceManager

# 配置日志
logger = logging.getLogger(__name__)


def _get_db_session():
    """获取数据库会话"""
    engine = get_engine()
    SessionFactory = get_session_factory(engine)
    return SessionFactory()


def list_workflows(args: argparse.Namespace) -> Dict[str, Any]:
    """列出所有工作流定义

    Args:
        args: 命令行参数

    Returns:
        Dict[str, Any]: 工作流列表数据
    """
    db_session = _get_db_session()
    try:
        repo = WorkflowDefinitionRepository(db_session)
        workflows = repo.get_all()

        workflow_list = []
        for workflow in workflows:
            workflow_dict = workflow.to_dict()
            workflow_list.append(workflow_dict)

            if args and hasattr(args, "verbose") and args.verbose:
                print(f"🔹 {workflow.id}: {workflow.name}")
                print(f"  描述: {workflow.description or '无'}")
                print(f"  创建时间: {workflow.created_at}")
                print(f"  更新时间: {workflow.updated_at}")
                print()
            elif not hasattr(args, "no_print") or not args.no_print:
                print(f"🔹 {workflow.id}: {workflow.name}")

        return {"workflows": workflow_list, "count": len(workflow_list)}
    finally:
        db_session.close()


def view_workflow(args: argparse.Namespace) -> Dict[str, Any]:
    """查看工作流详情

    Args:
        args: 命令行参数

    Returns:
        Dict[str, Any]: 工作流详情数据
    """
    db_session = _get_db_session()
    try:
        workflow_id = args.id if hasattr(args, "id") else args

        repo = WorkflowDefinitionRepository(db_session)
        workflow = repo.get_by_id(workflow_id)

        if not workflow:
            print(f"工作流不存在: {workflow_id}")
            return {"error": "工作流不存在"}

        # 获取会话管理器，列出相关会话
        session_manager = FlowSessionManager(db_session)
        sessions = session_manager.list_sessions(workflow_id=workflow_id)

        # 显示工作流基本信息
        if not hasattr(args, "no_print") or not args.no_print:
            print(f"🔹 {workflow.name} (ID: {workflow.id})")
            print(f"描述: {workflow.description or '无'}")
            print(f"创建时间: {workflow.created_at}")
            print(f"更新时间: {workflow.updated_at}")

            # 显示工作流阶段
            if workflow.stages:
                print("\n阶段:")
                for i, stage in enumerate(workflow.stages):
                    print(f"  {i+1}. {stage.get('name', 'Unnamed Stage')} ({stage.get('id', 'unknown')})")
                    if hasattr(args, "verbose") and args.verbose:
                        print(f"     描述: {stage.get('description', '无')}")
            else:
                print("\n没有定义阶段")

            # 显示最近的会话
            if sessions:
                print("\n最近的会话:")
                for i, session in enumerate(sessions[:5]):  # 只显示最近5条
                    status_map = {
                        "ACTIVE": "🔄",
                        "PAUSED": "⏸️",
                        "COMPLETED": "✅",
                        "ABORTED": "❌",
                    }
                    status_icon = status_map.get(session.status, "❓")
                    print(f"  {status_icon} {session.id} - {session.name} ({session.status})")
                    print(f"     创建时间: {session.created_at}")
                    print(f"     更新时间: {session.updated_at}")
                    if hasattr(args, "verbose") and args.verbose and session.context:
                        print(f"     上下文: {session.context}")
                    print()

        # 构建结果数据
        result = workflow.to_dict()
        result["sessions"] = [session.to_dict() for session in sessions]
        return result
    finally:
        db_session.close()


def create_workflow(args: argparse.Namespace) -> Dict[str, Any]:
    """创建工作流

    Args:
        args: 命令行参数

    Returns:
        Dict[str, Any]: 创建结果
    """
    db_session = _get_db_session()
    try:
        repo = WorkflowDefinitionRepository(db_session)

        # 创建工作流
        workflow_id = str(uuid.uuid4())
        workflow_data = {
            "id": workflow_id,
            "name": args.name,
            "description": args.description if hasattr(args, "description") else None,
            "type": args.type if hasattr(args, "type") else "generic",
            "stages": [],
        }

        workflow = repo.create(workflow_data)
        print(f"成功创建工作流: {workflow.name} (ID: {workflow.id})")

        return {"success": True, "workflow": workflow.to_dict()}
    except Exception as e:
        logger.error(f"创建工作流时出错: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def update_workflow(args: argparse.Namespace) -> Dict[str, Any]:
    """更新工作流

    Args:
        args: 命令行参数

    Returns:
        Dict[str, Any]: 更新结果
    """
    db_session = _get_db_session()
    try:
        repo = WorkflowDefinitionRepository(db_session)
        workflow = repo.get_by_id(args.id)
        if not workflow:
            print(f"工作流不存在: {args.id}")
            return {"success": False, "error": "工作流不存在"}

        # 准备更新数据
        update_data = {}
        if hasattr(args, "name") and args.name is not None:
            update_data["name"] = args.name
        if hasattr(args, "description") and args.description is not None:
            update_data["description"] = args.description
        if hasattr(args, "type") and args.type is not None:
            update_data["type"] = args.type
        if hasattr(args, "stages") and args.stages is not None:
            update_data["stages"] = args.stages

        # 更新工作流
        if update_data:
            workflow = repo.update(args.id, update_data)
            print(f"成功更新工作流: {workflow.name} (ID: {workflow.id})")
            return {"success": True, "workflow": workflow.to_dict()}
        else:
            print("没有提供更新数据")
            return {"success": False, "error": "没有提供更新数据"}
    except Exception as e:
        logger.error(f"更新工作流时出错: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def delete_workflow(args: argparse.Namespace) -> Dict[str, Any]:
    """删除工作流

    Args:
        args: 命令行参数

    Returns:
        Dict[str, Any]: 删除结果
    """
    db_session = _get_db_session()
    try:
        repo = WorkflowDefinitionRepository(db_session)
        workflow = repo.get_by_id(args.id)
        if not workflow:
            print(f"工作流不存在: {args.id}")
            return {"success": False, "error": "工作流不存在"}

        # 确认删除
        if not hasattr(args, "force") or not args.force:
            confirm = input(f"确定要删除工作流 '{workflow.name}' (ID: {workflow.id})? [y/N] ")
            if confirm.lower() != "y":
                print("已取消删除")
                return {"success": False, "cancelled": True}

        # 删除工作流
        workflow_data = workflow.to_dict()  # 保存数据用于返回
        repo.delete(args.id)
        print(f"成功删除工作流: {workflow.name} (ID: {workflow.id})")

        return {"success": True, "workflow": workflow_data}
    except Exception as e:
        logger.error(f"删除工作流时出错: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def execute_workflow(args: argparse.Namespace) -> Dict[str, Any]:
    """执行工作流(使用会话API)

    Args:
        args: 命令行参数

    Returns:
        Dict[str, Any]: 执行结果
    """
    db_session = _get_db_session()
    try:
        # 获取工作流定义
        workflow_id = args.id

        # 创建新会话
        session_manager = FlowSessionManager(db_session)
        session_name = f"执行-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        session = session_manager.create_session(workflow_id, name=session_name)

        if not session:
            return {"success": False, "error": "创建会话失败"}

        print(f"已创建工作流会话: {session.name} (ID: {session.id})")
        print(f"可以使用以下命令查看会话状态:")
        print(f"  vc flow session show {session.id}")

        return {"success": True, "session": session.to_dict()}
    except Exception as e:
        logger.error(f"执行工作流时出错: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def get_workflow(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    获取指定ID的工作流

    Args:
        workflow_id: 工作流ID

    Returns:
        工作流定义，如果未找到则返回None
    """
    db_session = _get_db_session()
    try:
        repo = WorkflowDefinitionRepository(db_session)
        workflow = repo.get_by_id(workflow_id)
        if workflow:
            return workflow.to_dict()
        return None
    finally:
        db_session.close()


def get_workflow_by_name(workflow_name: str) -> Optional[Dict[str, Any]]:
    """
    通过工作流名称获取工作流

    支持多种名称格式：dev, dev-flow, dev_flow 等，不区分大小写

    Args:
        workflow_name: 工作流名称

    Returns:
        工作流定义，如果未找到则返回None
    """
    db_session = _get_db_session()
    try:
        repo = WorkflowDefinitionRepository(db_session)
        workflow_name = workflow_name.lower().strip()

        # 尝试直接通过ID查找
        workflow = repo.get_by_id(workflow_name)
        if workflow:
            return workflow.to_dict()

        # 搜索所有工作流
        workflows = repo.get_all()
        for workflow in workflows:
            # 匹配名称或ID
            if workflow.name.lower() == workflow_name or workflow_name in workflow.name.lower() or workflow_name in workflow.id.lower():
                return workflow.to_dict()

        return None
    finally:
        db_session.close()


def get_workflow_context(args: argparse.Namespace) -> Dict[str, Any]:
    """获取工作流上下文

    Args:
        args: 命令行参数，包含workflow_id和progress_data

    Returns:
        Dict[str, Any]: 工作流上下文
    """
    workflow_id = args.workflow_id
    progress_data = args.progress_data if hasattr(args, "progress_data") else {}

    # 获取工作流定义
    workflow = get_workflow(workflow_id)
    if not workflow:
        return {"error": f"工作流不存在: {workflow_id}"}

    # 构建上下文
    context = {
        "workflow": workflow,
        "progress": progress_data,
        "timestamp": datetime.now().isoformat(),
    }

    return context


def sync_n8n(args: argparse.Namespace) -> Dict[str, Any]:
    """同步n8n工作流(已废弃)

    Args:
        args: 命令行参数

    Returns:
        Dict[str, Any]: 同步结果
    """
    return {"success": False, "error": "n8n集成已废弃，请使用flow_session API"}


# 为向后兼容性保留的别名
get_workflow_by_type = get_workflow_by_name
