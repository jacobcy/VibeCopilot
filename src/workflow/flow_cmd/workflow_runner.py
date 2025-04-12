#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流解释器

提供工作流阶段的解释和指导功能，使用flow_session管理工作流状态
作为解释器，不执行实际业务流程，而是提供上下文和指导
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from src.db import get_session_factory, init_db
from src.flow_session import FlowSessionManager, StageInstanceManager
from src.workflow.operations import get_workflow, get_workflow_by_id, get_workflow_by_type
from src.workflow.workflow_advanced_operations import save_execution

logger = logging.getLogger(__name__)


def run_workflow_stage(
    stage_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    session_id: Optional[str] = None,
    context_data: Optional[Dict[str, Any]] = None,
    completed_items: Optional[List[str]] = None,
    instance_name: Optional[str] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    解释工作流的特定阶段，提供定义和上下文指导。

    作为工作流解释器，此函数不执行实际业务流程，而是提供关于阶段定义和期望的指导。
    它管理工作流会话的元数据状态，跟踪进度和上下文，但不触发实际业务逻辑的执行。

    Args:
        stage_id: 要解释的阶段ID（如果提供了session_id则可选）
        workflow_id: 工作流ID（如果未提供session_id则必需）
        session_id: 现有会话的ID（如果未提供workflow_id则必需）
        context_data: 要添加到解释上下文的附加数据
        completed_items: 标记为已完成的项目列表
        instance_name: 会话实例的名称（创建新会话时使用）

    Returns:
        包含以下内容的元组：
            - 成功标志(True/False)
            - 消息字符串
            - 包含session_id、workflow_id、stage_id和上下文的数据字典
    """
    # Input validation
    if not workflow_id and not session_id:
        error_msg = "必须提供workflow_id或session_id其中之一"
        logger.error(error_msg)
        return False, error_msg, {}

    # Initialize response data
    response_data = {"session_id": session_id, "workflow_id": workflow_id, "stage_id": stage_id}

    try:
        # 如果提供了session_id但没有workflow_id，先从会话中获取workflow_id
        if session_id and not workflow_id:
            try:
                # 初始化数据库
                init_db()
                SessionFactory = get_session_factory()

                with SessionFactory() as db_session:
                    # 获取会话信息
                    session_manager = FlowSessionManager(db_session)
                    session = session_manager.get_session(session_id)

                    if not session:
                        error_msg = f"找不到ID为 {session_id} 的会话"
                        logger.error(error_msg)
                        return False, error_msg, response_data

                    # 从会话中获取workflow_id
                    workflow_id = session.workflow_id
                    if not workflow_id:
                        error_msg = f"会话 {session_id} 没有关联的工作流ID"
                        logger.error(error_msg)
                        return False, error_msg, response_data

                    # 如果没有提供stage_id，尝试获取会话当前阶段
                    if not stage_id and session.current_stage_id:
                        stage_id = session.current_stage_id
                        logger.info(f"使用会话中的当前阶段: {stage_id}")
                        response_data["stage_id"] = stage_id

                    logger.info(f"从会话 {session_id} 中获取到工作流ID: {workflow_id}")
                    response_data["workflow_id"] = workflow_id
            except Exception as e:
                error_msg = f"从会话获取工作流ID时出错: {str(e)}"
                logger.error(error_msg)
                return False, error_msg, response_data

        # 如果仍然没有stage_id，返回错误
        if not stage_id:
            error_msg = f"未提供阶段ID且在会话中未找到阶段ID"
            logger.error(error_msg)
            return False, error_msg, response_data

        # 获取或初始化解释上下文
        if session_id:
            logger.info(f"获取会话 {session_id} 的解释上下文")
            exec_context = get_workflow_context(session_id)
            if not exec_context:
                error_msg = f"未找到会话 {session_id} 的解释上下文"
                logger.error(error_msg)
                return False, error_msg, response_data

            # 确保workflow_id存在
            if not workflow_id:
                workflow_id = exec_context.get("workflow_id")
                if not workflow_id:
                    error_msg = f"无法确定会话 {session_id} 的工作流ID"
                    logger.error(error_msg)
                    return False, error_msg, response_data

            response_data["workflow_id"] = workflow_id
        else:
            logger.info(f"为工作流 {workflow_id} 初始化新的解释上下文")

            # 先检查工作流是否存在
            workflow = get_workflow_by_id(workflow_id)
            if not workflow:
                error_msg = f"找不到ID为 {workflow_id} 的工作流"
                logger.error(error_msg)
                return False, error_msg, response_data

            # 确保使用正确的工作流ID
            actual_workflow_id = workflow.get("id", workflow_id)
            if actual_workflow_id != workflow_id:
                logger.info(f"使用工作流实际ID: {actual_workflow_id} (而不是: {workflow_id})")
                workflow_id = actual_workflow_id
                response_data["workflow_id"] = workflow_id

            # 创建新的解释上下文和会话ID
            short_uuid = uuid4().hex[:12]
            session_id = f"session-{short_uuid}"
            exec_context = {
                "workflow_id": workflow_id,
                "session_id": session_id,
                "completed": [],
                "context": {},
                "current_stage": stage_id,
                "name": instance_name or f"Session_{workflow_id}_{short_uuid[:8]}",
            }
            response_data["session_id"] = session_id

            # 创建实际的FlowSession记录
            try:
                # 初始化数据库
                init_db()
                SessionFactory = get_session_factory()

                with SessionFactory() as db_session:
                    # 创建新的工作流会话
                    session_manager = FlowSessionManager(db_session)

                    try:
                        flow_session = session_manager.create_session(workflow_id=workflow_id, name=exec_context["name"])

                        # 更新解释上下文中的会话ID
                        session_id = flow_session.id
                        exec_context["session_id"] = session_id
                        response_data["session_id"] = session_id

                        logger.info(f"创建了新的工作流会话: {session_id}")
                    except ValueError as e:
                        logger.error(f"创建工作流会话失败: {str(e)}")
                        error_msg = f"无法创建工作流会话: {str(e)}"
                        return False, error_msg, response_data
            except Exception as e:
                logger.error(f"创建工作流会话失败: {str(e)}")
                error_msg = f"创建工作流会话过程中出错: {str(e)}"
                return False, error_msg, response_data

        # 如果是继续现有会话的情况，需要在这里获取工作流
        if session_id and not "workflow" in locals():
            workflow = get_workflow_by_id(workflow_id)
            if not workflow:
                error_msg = f"找不到ID为 {workflow_id} 的工作流"
                logger.error(error_msg)
                return False, error_msg, response_data

        # 验证阶段是否存在于工作流中
        stages = workflow.get("stages", [])
        stage_found = False
        stage_name = None
        for stage in stages:
            if stage.get("id") == stage_id:
                stage_found = True
                stage_name = stage.get("name", stage_id)
                break

        if not stage_found:
            error_msg = f"在工作流 {workflow_id} 中找不到阶段 '{stage_id}'"
            logger.error(error_msg)
            return False, error_msg, response_data

        # 如果提供了已完成项目，更新上下文
        if completed_items:
            if "completed" not in exec_context:
                exec_context["completed"] = []

            for item in completed_items:
                if item not in exec_context["completed"]:
                    exec_context["completed"].append(item)

        # 如果提供了附加上下文数据，进行添加
        if context_data:
            if "context" not in exec_context:
                exec_context["context"] = {}

            exec_context["context"].update(context_data)

        # 更新当前阶段
        exec_context["current_stage"] = stage_id

        # 保存解释上下文
        saved_context = save_execution(exec_context)
        if not saved_context:
            error_msg = "保存解释上下文失败"
            logger.error(error_msg)
            return False, error_msg, response_data

        # 更新响应数据中的工作流名称和阶段名称
        # 我们已经在前面获取了工作流，可以直接使用
        if "workflow" in locals():
            response_data["context"] = exec_context.get("context", {})
            response_data["completed"] = exec_context.get("completed", [])
            response_data["workflow_name"] = workflow.get("name", "未知工作流")
            response_data["stage_name"] = stage_name

            success_message = f"成功准备工作会话 '{workflow.get('name')}' 的 '{stage_name}' 阶段"

            # 更新会话当前阶段
            try:
                # 初始化数据库
                init_db()
                SessionFactory = get_session_factory()

                with SessionFactory() as db_session:
                    # 更新会话的当前阶段
                    session_manager = FlowSessionManager(db_session)
                    session = session_manager.get_session(session_id)

                    if session and session.current_stage_id != stage_id:
                        # 更新会话当前阶段
                        updated_session = session_manager.update_session(session_id=session_id, current_stage_id=stage_id)
                        if updated_session:
                            logger.info(f"已更新会话 {session_id} 的当前阶段为 {stage_id}")
                        else:
                            logger.warning(f"未能更新会话 {session_id} 的当前阶段")

                    # 创建阶段实例（如果需要）
                    stage_manager = StageInstanceManager(db_session)
                    try:
                        # 检查是否已存在阶段实例
                        existing_instance = stage_manager.get_current_stage_instance(session_id)

                        if existing_instance and existing_instance.stage_id == stage_id:
                            logger.info(f"已存在阶段实例 {existing_instance.id} 用于阶段 {stage_id}")
                        else:
                            # 创建新的阶段实例
                            stage_instance = stage_manager.create_stage_instance(session_id=session_id, stage_id=stage_id)
                            logger.info(f"已创建新的阶段实例 {stage_instance.id} 用于阶段 {stage_id}")
                    except Exception as e:
                        logger.warning(f"创建阶段实例时出错: {str(e)}")
            except Exception as e:
                logger.warning(f"更新会话阶段时出错: {str(e)}")

            # 返回成功结果
            # 注意：作为解释器，我们只提供工作流阶段的定义和上下文，不执行实际业务流程
            return True, success_message, response_data
        else:
            error_msg = "未能加载工作流信息"
            logger.error(error_msg)
            return False, error_msg, response_data

    except Exception as e:
        error_msg = f"解释工作流阶段时出错: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, response_data


def complete_workflow_stage(stage_instance_id: str, output: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    标记工作流阶段为已完成并记录输出。

    作为工作流解释器，此函数仅更新阶段实例的状态和元数据，
    不会触发实际业务流程的执行或完成。

    Args:
        stage_instance_id: 要标记为完成的阶段实例ID
        output: 阶段输出数据（可选）

    Returns:
        元组包含：
        - 成功标志(True/False)
        - 消息字符串
        - 可选的数据字典
    """
    try:
        # 初始化数据库连接
        init_db()
        SessionFactory = get_session_factory()

        with SessionFactory() as db_session:
            # 获取阶段实例
            stage_manager = StageInstanceManager(db_session)
            stage_instance = stage_manager.get_stage_instance(stage_instance_id)

            if not stage_instance:
                error_msg = f"找不到ID为 {stage_instance_id} 的阶段实例"
                logger.error(error_msg)
                return False, error_msg, None

            # 更新阶段实例状态和输出
            updated_instance = stage_manager.update_stage_instance(instance_id=stage_instance_id, status="completed", output=output)

            if not updated_instance:
                error_msg = f"更新阶段实例 {stage_instance_id} 失败"
                logger.error(error_msg)
                return False, error_msg, None

            logger.info(f"已将阶段实例 {stage_instance_id} 标记为已完成")
            return True, f"阶段已标记为完成", {"stage_instance_id": stage_instance_id}

    except Exception as e:
        error_msg = f"完成工作流阶段时出错: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, None


def get_workflow_context(session_id: str) -> Dict[str, Any]:
    """
    获取工作流会话的解释上下文

    查询特定会话的当前上下文数据，包括完成的项目、当前阶段和上下文变量。
    作为解释器，这只是元数据查询，不会执行或触发实际的阶段业务流程。

    Args:
        session_id: 会话ID

    Returns:
        包含会话上下文的字典，如果未找到则返回空字典
    """
    try:
        # 尝试从会话元数据获取上下文
        from src.workflow.workflow_advanced_operations import get_execution

        # 查询会话
        context = get_execution(session_id)
        if context:
            return context

        # 如果没有找到已保存的上下文，返回空对象
        return {}
    except Exception as e:
        logger.error(f"获取工作流上下文时出错: {str(e)}")
        return {}
