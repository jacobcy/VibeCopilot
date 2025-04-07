#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流下一阶段推荐模块

提供推荐工作流下一执行阶段的功能
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from src.db import get_session_factory, init_db
from src.flow_session.session_manager import FlowSessionManager
from src.flow_session.stage_manager import StageInstanceManager
from src.workflow.exporters.json_exporter import JsonExporter

logger = logging.getLogger(__name__)


def handle_next_stage(
    session_id: str,
    current_stage_instance_id: Optional[str] = None,
    format_type: str = "text",
    verbose: bool = False,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理获取工作流下一阶段推荐的命令

    Args:
        session_id: 工作流会话ID
        current_stage_instance_id: 当前阶段实例ID（可选，如不提供则自动识别）
        format_type: 输出格式（"text"或"json"）
        verbose: 是否显示详细信息

    Returns:
        包含状态、消息和推荐数据的元组
    """
    try:
        engine = init_db()
        SessionFactory = get_session_factory(engine)

        with SessionFactory() as db_session:
            # 获取会话信息
            session_manager = FlowSessionManager(db_session)
            flow_session = session_manager.get_session(session_id)

            if not flow_session:
                return False, f"找不到会话: '{session_id}'", None

            # 检查会话状态
            if flow_session.status != "ACTIVE":
                return False, f"会话 '{session_id}' 不处于活动状态 (当前: {flow_session.status})", None

            # 获取工作流定义
            exporter = JsonExporter()
            workflow = exporter.load_workflow(flow_session.workflow_id)

            if not workflow:
                return False, f"找不到工作流定义: '{flow_session.workflow_id}'", None

            # 获取会话中的阶段实例
            stage_manager = StageInstanceManager(db_session)
            stage_instances = session_manager.get_session_stages(session_id)
            stage_instances_by_id = {s.id: s for s in stage_instances}

            # 如果提供了当前阶段实例ID，验证其存在性
            current_instance = None
            if current_stage_instance_id:
                if current_stage_instance_id in stage_instances_by_id:
                    current_instance = stage_instances_by_id[current_stage_instance_id]
                else:
                    return False, f"在会话中找不到阶段实例: '{current_stage_instance_id}'", None
            else:
                # 从会话中获取当前阶段
                current_stage_id = flow_session.current_stage_id
                if current_stage_id:
                    # 查找对应的最新实例
                    active_instances = [
                        s
                        for s in stage_instances
                        if s.stage_id == current_stage_id and s.status != "COMPLETED"
                    ]
                    if active_instances:
                        current_instance = active_instances[0]  # 取最新的

            # 分析已完成的阶段
            completed_stages = set()
            active_stage_id = None

            for instance in stage_instances:
                if instance.status == "COMPLETED":
                    completed_stages.add(instance.stage_id)
                elif instance.status == "ACTIVE" and not active_stage_id:
                    active_stage_id = instance.stage_id

            # 获取工作流中的阶段定义
            stages = workflow.get("stages", [])
            stages_by_id = {s.get("id"): s for s in stages}

            # 构建阶段依赖关系图
            dependencies = {}
            for stage in stages:
                stage_id = stage.get("id")
                stage_deps = stage.get("dependencies", [])
                dependencies[stage_id] = stage_deps

            # 查找下一个可执行的阶段
            next_stages = []
            for stage in stages:
                stage_id = stage.get("id")

                # 跳过已完成的阶段
                if stage_id in completed_stages or stage_id == active_stage_id:
                    continue

                # 检查依赖关系
                deps = dependencies.get(stage_id, [])
                can_execute = True
                for dep in deps:
                    if dep not in completed_stages:
                        can_execute = False
                        break

                if can_execute:
                    next_stages.append(stage)

            # 准备结果数据
            result = {
                "session_id": session_id,
                "workflow_id": flow_session.workflow_id,
                "workflow_name": workflow.get("name", "未命名工作流"),
                "current_stage": None,
                "recommended_stages": [],
            }

            # 设置当前阶段信息
            if current_instance:
                stage_info = stages_by_id.get(current_instance.stage_id, {})
                result["current_stage"] = {
                    "instance_id": current_instance.id,
                    "id": current_instance.stage_id,
                    "name": stage_info.get("name", current_instance.stage_id),
                    "description": stage_info.get("description", ""),
                    "status": current_instance.status,
                }

                # 获取阶段进度
                if current_instance.status == "ACTIVE":
                    progress = stage_manager.get_instance_progress(current_instance.id)
                    items = progress.get("items", [])
                    total = len(items)
                    completed = sum(1 for item in items if item.get("status") == "COMPLETED")

                    if total > 0:
                        result["current_stage"]["progress"] = {
                            "completed": completed,
                            "total": total,
                            "percentage": round(completed / total * 100) if total > 0 else 0,
                        }

            # 设置推荐阶段信息
            for stage in next_stages:
                stage_id = stage.get("id")
                stage_info = {
                    "id": stage_id,
                    "name": stage.get("name", stage_id),
                    "description": stage.get("description", ""),
                    "dependencies": dependencies.get(stage_id, []),
                    "required_deliverables": stage.get("required_deliverables", []),
                }

                # 添加执行命令
                stage_info[
                    "command"
                ] = f"vibecopilot flow run {workflow.get('type', 'workflow')}:{stage_id} --session={session_id}"

                result["recommended_stages"].append(stage_info)

            # 根据格式生成响应
            if format_type == "json":
                return True, json.dumps(result, ensure_ascii=False, indent=2), result
            else:
                # 文本格式输出
                message = f"📋 下一阶段推荐 (会话ID: {session_id})\n"
                message += f"工作流: {result['workflow_name']} (ID: {result['workflow_id']})\n\n"

                # 显示当前阶段
                if result["current_stage"]:
                    current = result["current_stage"]
                    message += "当前阶段:\n"
                    message += f"- {current['name']} ({current['id']})\n"
                    message += f"- 状态: {current['status']}\n"

                    if "progress" in current:
                        progress = current["progress"]
                        message += f"- 进度: {progress['completed']}/{progress['total']} ({progress['percentage']}%)\n"

                    message += "\n完成当前阶段后，可以执行以下阶段:\n"
                else:
                    message += "当前没有活动阶段，可以执行以下阶段:\n"

                # 显示推荐阶段
                if result["recommended_stages"]:
                    for i, stage in enumerate(result["recommended_stages"], 1):
                        message += f"\n选项 {i}: {stage['name']}\n"
                        message += f"- 描述: {stage['description']}\n"

                        if stage["dependencies"]:
                            deps = [
                                stages_by_id.get(d, {}).get("name", d)
                                for d in stage["dependencies"]
                            ]
                            message += f"- 依赖阶段: {', '.join(deps)}\n"

                        message += f"- 执行命令:\n  {stage['command']}\n"
                else:
                    message += "\n没有可执行的下一阶段。可能所有阶段已完成或依赖条件未满足。\n"

                if verbose:
                    # 添加帮助提示
                    message += "\n使用命令 'vibecopilot flow session show " + session_id + "' 查看完整会话状态。"

                return True, message, result

    except Exception as e:
        logger.exception(f"获取下一阶段建议时出错: {session_id}")
        return False, f"获取下一阶段建议时出错: {str(e)}", None
