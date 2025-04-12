"""
Flow 'visualize' subcommand handler.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import get_session_factory
from src.flow_session.session.manager import FlowSessionManager
from src.models.db import FlowSession, WorkflowDefinition
from src.workflow.operations import get_workflow

logger = logging.getLogger(__name__)


def handle_visualize_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理可视化子命令

    Args:
        args: 命令参数 (来自 argparse)
            - id: 工作流ID或会话ID
            - session: 是否可视化会话而不是工作流定义
            - format: 输出格式 (mermaid 或 text)
            - output: 输出文件路径
            - verbose: 是否显示详细信息

    Returns:
        命令结果字典
    """
    target_id = args.get("id")
    is_session = args.get("session", False)
    output_format = args.get("format", "mermaid")
    output_file = args.get("output")
    verbose = args.get("verbose", False)

    if verbose:
        logger.debug(f"可视化参数: id={target_id}, is_session={is_session}, format={output_format}")

    try:
        # 创建数据库会话
        session_factory = get_session_factory()
        db_session = session_factory()

        if is_session:
            # 可视化会话
            result = visualize_session(db_session, target_id, output_format)
        else:
            # 可视化工作流定义
            result = visualize_workflow(db_session, target_id, output_format)

        # 释放数据库会话
        db_session.close()

        # 如果需要输出到文件
        if output_file and result:
            dir_path = os.path.dirname(output_file)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result)

            return {
                "status": "success",
                "code": 200,
                "message": f"已将可视化结果保存到文件: {output_file}",
                "data": {"diagram": result},
                "meta": {"command": "flow visualize", "args": args},
            }

        # 直接返回可视化结果
        return {
            "status": "success",
            "code": 200,
            "message": result,
            "data": {"diagram": result},
            "meta": {"command": "flow visualize", "args": args},
        }

    except Exception as e:
        logger.error(f"可视化失败: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "code": 500,
            "message": f"可视化失败: {str(e)}",
            "data": None,
            "meta": {"command": "flow visualize", "args": args},
        }


def visualize_workflow(db_session: Session, workflow_id: str, output_format: str) -> str:
    """
    可视化工作流定义

    Args:
        db_session: 数据库会话
        workflow_id: 工作流ID
        output_format: 输出格式

    Returns:
        可视化结果字符串
    """
    # 获取工作流定义
    workflow = get_workflow(workflow_id)

    if not workflow:
        raise ValueError(f"找不到ID为 {workflow_id} 的工作流")

    # 获取阶段信息
    stages = workflow.get("stages", {})
    if isinstance(stages, str):
        try:
            stages = json.loads(stages)
        except:
            stages = {}

    # 生成可视化内容
    if output_format == "mermaid":
        return generate_workflow_mermaid(workflow, stages)
    else:
        return generate_workflow_text(workflow, stages)


def visualize_session(db_session: Session, session_id: str, output_format: str) -> str:
    """
    可视化会话及其进度

    Args:
        db_session: 数据库会话
        session_id: 会话ID
        output_format: 输出格式

    Returns:
        可视化结果字符串
    """
    # 获取会话信息
    manager = FlowSessionManager(db_session)
    session = manager.get_session(session_id)

    if not session:
        raise ValueError(f"找不到ID为 {session_id} 的会话")

    # 获取工作流定义
    workflow_id = session.workflow_id
    workflow = get_workflow(workflow_id)

    if not workflow:
        raise ValueError(f"找不到会话关联的工作流定义 (ID: {workflow_id})")

    # 获取会话进度
    progress_info = manager.get_session_progress(session_id)

    # 生成可视化内容
    if output_format == "mermaid":
        return generate_session_mermaid(session, workflow, progress_info)
    else:
        return generate_session_text(session, workflow, progress_info)


def generate_workflow_mermaid(workflow: Dict[str, Any], stages: Dict[str, Any]) -> str:
    """
    生成工作流的Mermaid图表

    Args:
        workflow: 工作流定义
        stages: 阶段信息

    Returns:
        Mermaid图表字符串
    """
    workflow_id = workflow.get("id", "未知")
    workflow_name = workflow.get("name", workflow_id)

    mermaid = [
        "```mermaid",
        "flowchart TD",
        f'    title["工作流: {workflow_name}"]',
        "    style title fill:#f9f,stroke:#333,stroke-width:2px",
    ]

    # 添加阶段节点
    stage_nodes = []
    for stage_id, stage_info in stages.items():
        if isinstance(stage_info, dict):
            stage_name = stage_info.get("name", stage_id)
            stage_nodes.append(f'    {stage_id}["{stage_name}"]')

    mermaid.extend(stage_nodes)

    # 添加连接关系
    connections = []
    stage_ids = list(stages.keys())
    for i in range(len(stage_ids) - 1):
        current_id = stage_ids[i]
        next_id = stage_ids[i + 1]
        connections.append(f"    {current_id} --> {next_id}")

    mermaid.extend(connections)
    mermaid.append("```")

    return "\n".join(mermaid)


def generate_workflow_text(workflow: Dict[str, Any], stages: Dict[str, Any]) -> str:
    """
    生成工作流的文本表示

    Args:
        workflow: 工作流定义
        stages: 阶段信息

    Returns:
        文本表示字符串
    """
    workflow_id = workflow.get("id", "未知")
    workflow_name = workflow.get("name", workflow_id)

    lines = [
        f"工作流: {workflow_name} (ID: {workflow_id})",
        "=" * 40,
        "阶段列表:",
    ]

    # 添加阶段信息
    for stage_id, stage_info in stages.items():
        if isinstance(stage_info, dict):
            stage_name = stage_info.get("name", stage_id)
            lines.append(f"- {stage_name} (ID: {stage_id})")

    return "\n".join(lines)


def generate_session_mermaid(session: FlowSession, workflow: Dict[str, Any], progress: Dict[str, Any]) -> str:
    """
    生成会话的Mermaid图表，包括进度信息

    Args:
        session: 会话信息
        workflow: 工作流定义
        progress: 进度信息

    Returns:
        Mermaid图表字符串
    """
    workflow_id = workflow.get("id", "未知")
    workflow_name = workflow.get("name", workflow_id)
    session_name = session.name

    # 获取阶段状态
    completed_stage_ids = [s.get("id") for s in progress.get("completed_stages", [])]
    current_stage_id = progress.get("current_stage", {}).get("id")

    # 计算进度
    progress_percent = progress.get("progress_percentage", 0)
    completed_count = progress.get("completed_count", 0)
    total_stages = progress.get("total_stages", 0)

    mermaid = [
        "```mermaid",
        "flowchart TD",
        f'    title["会话: {session_name} ({progress_percent}% 完成)"]',
        "    style title fill:#f9f,stroke:#333,stroke-width:2px",
        f'    subTitle["工作流: {workflow_name} | 已完成: {completed_count}/{total_stages}"]',
        "    style subTitle fill:#ddf,stroke:#333,stroke-width:1px",
        "    title --> subTitle",
    ]

    # 获取阶段
    stages = workflow.get("stages", {})
    if isinstance(stages, str):
        try:
            stages = json.loads(stages)
        except:
            stages = {}

    # 添加阶段节点
    stage_nodes = []
    for stage_id, stage_info in stages.items():
        if not isinstance(stage_info, dict):
            continue

        stage_name = stage_info.get("name", stage_id)

        # 根据阶段状态设置样式
        style = ""
        if stage_id in completed_stage_ids:
            # 已完成阶段
            stage_nodes.append(f'    {stage_id}["{stage_name}"]')
            style = f"    style {stage_id} fill:#9f9,stroke:#333,stroke-width:1px"
        elif stage_id == current_stage_id:
            # 当前阶段
            stage_nodes.append(f'    {stage_id}["{stage_name}"]')
            style = f"    style {stage_id} fill:#ff9,stroke:#333,stroke-width:2px"
        else:
            # 待处理阶段
            stage_nodes.append(f'    {stage_id}["{stage_name}"]')
            style = f"    style {stage_id} fill:#ddd,stroke:#333,stroke-width:1px"

        stage_nodes.append(style)

    mermaid.extend(stage_nodes)

    # 添加阶段连接
    connections = []
    stage_ids = list(stages.keys())
    for i in range(len(stage_ids) - 1):
        current_id = stage_ids[i]
        next_id = stage_ids[i + 1]
        connections.append(f"    {current_id} --> {next_id}")

    # 将开始节点连接到第一个阶段
    if stage_ids:
        connections.append(f"    subTitle --> {stage_ids[0]}")

    mermaid.extend(connections)
    mermaid.append("```")

    return "\n".join(mermaid)


def generate_session_text(session: FlowSession, workflow: Dict[str, Any], progress: Dict[str, Any]) -> str:
    """
    生成会话的文本表示，包括进度信息

    Args:
        session: 会话信息
        workflow: 工作流定义
        progress: 进度信息

    Returns:
        文本表示字符串
    """
    workflow_id = workflow.get("id", "未知")
    workflow_name = workflow.get("name", workflow_id)
    session_name = session.name

    # 计算进度
    progress_percent = progress.get("progress_percentage", 0)
    completed_count = progress.get("completed_count", 0)
    total_stages = progress.get("total_stages", 0)

    lines = [
        f"会话: {session_name} (ID: {session.id})",
        f"工作流: {workflow_name} (ID: {workflow_id})",
        f"状态: {session.status}",
        f"进度: {progress_percent}% 完成 ({completed_count}/{total_stages} 阶段)",
        "=" * 40,
        "阶段状态:",
    ]

    # 已完成阶段
    for stage in progress.get("completed_stages", []):
        completed_at = stage.get("completed_at", "")
        if completed_at:
            # 简化时间格式
            completed_at = completed_at.split("T")[0] + " " + completed_at.split("T")[1][:5]
            lines.append(f"✅ {stage['name']} - 已完成 ({completed_at})")
        else:
            lines.append(f"✅ {stage['name']} - 已完成")

    # 当前阶段
    current_stage = progress.get("current_stage")
    if current_stage:
        lines.append(f"▶️ {current_stage['name']} - 进行中")

    # 待处理阶段
    for stage in progress.get("pending_stages", []):
        lines.append(f"⏳ {stage['name']} - 待进行")

    return "\n".join(lines)
