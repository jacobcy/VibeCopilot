"""
工作流运行器模块

处理工作流执行和上下文管理
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.db import get_session_factory, init_db
from src.flow_session import FlowSessionManager, StageInstanceManager
from src.workflow.interpreter.context_provider import ContextProvider
from src.workflow.workflow_operations import get_workflow, get_workflow_by_type

logger = logging.getLogger(__name__)


def get_workflow_context(workflow_id: str, progress_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取工作流上下文

    Args:
        workflow_id: 工作流ID
        progress_data: 进度数据

    Returns:
        工作流上下文
    """
    context_provider = ContextProvider()
    return context_provider.provide_context_to_agent(workflow_id, progress_data)


def run_workflow_stage(
    workflow_name: str,
    stage_name: str,
    instance_name: Optional[str] = None,
    completed_items: Optional[List[str]] = None,
    session_id: Optional[str] = None,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    运行工作流的特定阶段

    Args:
        workflow_name: 工作流名称
        stage_name: 阶段名称
        instance_name: 阶段实例名称（可选）
        completed_items: 已完成的检查项列表（可选）
        session_id: 会话ID（可选）

    Returns:
        包含运行状态、消息和结果数据的元组
    """
    try:
        # 检查工作流是否存在
        workflow = get_workflow_by_type(workflow_name)

        if not workflow:
            logger.error(f"找不到工作流: {workflow_name}")
            return False, f"找不到工作流: {workflow_name}", None

        # 验证阶段是否存在
        stage_info = None
        if workflow.get("stages"):
            for stage in workflow["stages"]:
                if (
                    stage.get("name", "").lower() == stage_name.lower()
                    or stage.get("id", "").lower() == stage_name.lower()
                ):
                    stage_info = stage
                    break

        if not stage_info:
            # 列出可用阶段
            available_stages = ""
            if workflow.get("stages"):
                stage_list = [f"  - {s.get('name')}" for s in workflow["stages"]]
                available_stages = "\n".join(stage_list)

            logger.error(f"工作流 {workflow_name} 中找不到阶段: {stage_name}")
            return (
                False,
                f"工作流 {workflow_name} 中找不到阶段: {stage_name}\n可用阶段:\n{available_stages}",
                None,
            )

        # 处理会话流程
        engine = init_db()
        SessionFactory = get_session_factory(engine)

        with SessionFactory() as db_session:
            # 如果提供了会话ID，使用现有会话
            if session_id:
                session_manager = FlowSessionManager(db_session)
                flow_session = session_manager.get_session(session_id)

                if not flow_session:
                    logger.error(f"找不到会话: {session_id}")
                    return False, f"找不到会话: {session_id}", None

                # 创建阶段实例
                stage_manager = StageInstanceManager(db_session)
                try:
                    stage_instance = stage_manager.create_instance(
                        session_id=session_id,
                        stage_id=stage_info.get("id"),
                        name=stage_info.get("name"),
                    )

                    # 启动阶段
                    stage_manager.start_instance(stage_instance.id)

                    # 如果有已完成项，添加到阶段实例
                    if completed_items:
                        for item_id in completed_items:
                            stage_manager.complete_check_item(stage_instance.id, item_id)

                    # 返回状态
                    return (
                        True,
                        f"成功启动阶段: {stage_info.get('name')}",
                        {
                            "session_id": session_id,
                            "stage_instance_id": stage_instance.id,
                            "stage": stage_info,
                        },
                    )
                except Exception as e:
                    logger.error(f"创建阶段实例时出错: {str(e)}")
                    return False, f"创建阶段实例时出错: {str(e)}", None
            else:
                # 创建新会话
                session_manager = FlowSessionManager(db_session)
                instance_name = instance_name or f"{workflow_name}_{stage_name}"

                try:
                    # 创建会话
                    flow_session = session_manager.create_session(
                        workflow_id=workflow.get("id"),
                        name=instance_name,
                    )

                    # 创建阶段实例
                    stage_manager = StageInstanceManager(db_session)
                    stage_instance = stage_manager.create_instance(
                        session_id=flow_session.id,
                        stage_id=stage_info.get("id"),
                        name=stage_info.get("name"),
                    )

                    # 启动阶段
                    stage_manager.start_instance(stage_instance.id)

                    # 如果有已完成项，添加到阶段实例
                    if completed_items:
                        for item_id in completed_items:
                            stage_manager.complete_check_item(stage_instance.id, item_id)

                    # 返回状态
                    return (
                        True,
                        f"成功创建会话并启动阶段: {stage_info.get('name')}",
                        {
                            "session_id": flow_session.id,
                            "stage_instance_id": stage_instance.id,
                            "stage": stage_info,
                        },
                    )
                except Exception as e:
                    logger.error(f"创建会话时出错: {str(e)}")
                    return False, f"创建会话时出错: {str(e)}", None
    except Exception as e:
        logger.error(f"运行工作流阶段时出错: {str(e)}")
        return False, f"运行工作流阶段时出错: {str(e)}", None


def complete_workflow_stage(
    stage_instance_id: str, output: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    完成工作流阶段

    Args:
        stage_instance_id: 阶段实例ID
        output: 阶段输出数据

    Returns:
        包含完成状态、消息和结果数据的元组
    """
    try:
        # 初始化数据库
        engine = init_db()
        SessionFactory = get_session_factory(engine)

        with SessionFactory() as db_session:
            # 获取阶段实例
            stage_manager = StageInstanceManager(db_session)
            stage_instance = stage_manager.get_instance(stage_instance_id)

            if not stage_instance:
                logger.error(f"找不到阶段实例: {stage_instance_id}")
                return False, f"找不到阶段实例: {stage_instance_id}", None

            # 完成阶段
            stage_manager.complete_instance(stage_instance_id, output)

            return (
                True,
                f"成功完成阶段: {stage_instance.name}",
                {"stage_instance_id": stage_instance_id, "output": output},
            )
    except Exception as e:
        logger.error(f"完成工作流阶段时出错: {str(e)}")
        return False, f"完成工作流阶段时出错: {str(e)}", None
