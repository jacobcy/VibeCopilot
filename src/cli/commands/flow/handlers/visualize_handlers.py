#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流可视化处理模块

提供工作流结构可视化功能
"""

import logging
import os
from typing import Any, Dict, Optional, Tuple

from src.db import get_session_factory, init_db
from src.flow_session.session_manager import FlowSessionManager
from src.flow_session.stage_manager import StageInstanceManager
from src.workflow.exporters.json_exporter import JsonExporter
from src.workflow.exporters.mermaid_exporter import MermaidExporter

logger = logging.getLogger(__name__)


def handle_visualize_workflow(
    id_value: str,
    is_session: bool = False,
    format_type: str = "mermaid",
    output_path: Optional[str] = None,
    verbose: bool = False,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    处理可视化工作流命令

    Args:
        id_value: 工作流ID或会话ID
        is_session: 是否为会话ID
        format_type: 输出格式 (mermaid, text)
        output_path: 输出文件路径（可选）
        verbose: 是否显示详细信息

    Returns:
        包含状态、消息和可视化数据的元组
    """
    try:
        # 初始化导出器
        json_exporter = JsonExporter()
        mermaid_exporter = MermaidExporter()
        workflow = None
        session_data = None

        # 处理会话可视化
        if is_session:
            engine = init_db()
            SessionFactory = get_session_factory(engine)

            with SessionFactory() as db_session:
                # 获取会话信息
                session_manager = FlowSessionManager(db_session)
                flow_session = session_manager.get_session(id_value)

                if not flow_session:
                    return False, f"找不到会话: '{id_value}'", None

                # 获取工作流定义
                workflow_id = flow_session.workflow_id
                workflow = json_exporter.load_workflow(workflow_id)

                if not workflow:
                    return False, f"找不到会话 '{id_value}' 的工作流定义: '{workflow_id}'", None

                # 获取会话阶段状态
                stage_manager = StageInstanceManager(db_session)
                stage_instances = session_manager.get_session_stages(id_value)

                # 创建会话状态数据
                session_data = {"completed_stages": [], "active_stages": [], "pending_stages": []}

                # 收集阶段实例状态
                stage_status = {}
                for instance in stage_instances:
                    if instance.status == "COMPLETED":
                        session_data["completed_stages"].append(instance.stage_id)
                        stage_status[instance.stage_id] = "COMPLETED"
                    elif instance.status == "ACTIVE":
                        session_data["active_stages"].append(instance.stage_id)
                        stage_status[instance.stage_id] = "ACTIVE"

                # 标记未开始的阶段
                all_stages = [s.get("id") for s in workflow.get("stages", [])]
                for stage_id in all_stages:
                    if stage_id not in stage_status:
                        session_data["pending_stages"].append(stage_id)
        else:
            # 直接获取工作流定义
            workflow = json_exporter.load_workflow(id_value)

            if not workflow:
                return False, f"找不到工作流: '{id_value}'", None

        # 生成可视化
        if format_type == "mermaid":
            if session_data:
                # 会话可视化，包含状态
                mermaid_code = mermaid_exporter.export_workflow_with_status(
                    workflow,
                    session_data["completed_stages"],
                    session_data["active_stages"],
                    session_data["pending_stages"],
                )
            else:
                # 普通工作流可视化
                mermaid_code = mermaid_exporter.export_workflow(workflow)

            # 写入文件或返回结果
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(mermaid_code)
                message = f"✅ 已将可视化输出保存到: {output_path}"
            else:
                message = f"📊 工作流可视化 ({id_value}):\n\n{mermaid_code}"

                # 添加图例说明
                if session_data:
                    message += "\n\n🔹 图例说明:"
                    message += "\n- 绿色: 已完成阶段"
                    message += "\n- 黄色: 进行中阶段"
                    message += "\n- 灰色: 未开始阶段"
                    message += "\n- 箭头: 阶段间依赖关系"

            return True, message, {"mermaid": mermaid_code, "workflow": workflow}
        else:
            # 文本格式
            stages = workflow.get("stages", [])

            message = f"📊 工作流结构 ({id_value}):\n\n"
            message += f"工作流: {workflow.get('name', '未命名')} (ID: {workflow.get('id', 'unknown')})\n"
            message += f"类型: {workflow.get('type', '未知')}\n"
            message += f"描述: {workflow.get('description', '无')}\n\n"

            if stages:
                message += f"阶段 ({len(stages)}):\n"

                for i, stage in enumerate(stages, 1):
                    stage_id = stage.get("id", f"stage_{i}")
                    stage_name = stage.get("name", stage_id)

                    # 添加状态信息
                    status = ""
                    if session_data:
                        if stage_id in session_data["completed_stages"]:
                            status = "✅ [已完成]"
                        elif stage_id in session_data["active_stages"]:
                            status = "▶️ [进行中]"
                        else:
                            status = "⏳ [未开始]"

                    message += f"\n{i}. {stage_name} ({stage_id}) {status}"

                    if "description" in stage and stage["description"]:
                        message += f"\n   描述: {stage['description']}"

                    dependencies = stage.get("dependencies", [])
                    if dependencies:
                        dep_names = []
                        for dep_id in dependencies:
                            for s in stages:
                                if s.get("id") == dep_id:
                                    dep_names.append(s.get("name", dep_id))
                                    break
                            else:
                                dep_names.append(dep_id)

                        message += f"\n   依赖: {', '.join(dep_names)}"
            else:
                message += "没有定义任何阶段\n"

            if is_session:
                message += f"\n\n使用 'vibecopilot flow session show {id_value}' 查看详细的会话状态。"

            if verbose:
                message += f"\n\n使用 --format=mermaid 参数获取图形化视图。"

            return True, message, {"text": message, "workflow": workflow}

    except Exception as e:
        logger.exception(f"可视化工作流时出错: {id_value}")
        return False, f"可视化工作流时出错: {str(e)}", None
