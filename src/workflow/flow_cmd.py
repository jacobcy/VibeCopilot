#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流命令行工具

提供工作流相关命令行操作
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from src.db import get_session_factory, init_db
from src.flow_session import FlowSessionManager, StageInstanceManager
from src.workflow.exporters.json_exporter import JsonExporter
from src.workflow.exporters.mermaid_exporter import MermaidExporter
from src.workflow.interpreter.context_provider import ContextProvider
from src.workflow.interpreter.flow_converter import FlowConverter
from src.workflow.interpreter.rule_parser import RuleParser
from src.workflow.template_loader import create_workflow_from_template, load_flow_template
from src.workflow.workflow_operations import get_workflow, get_workflow_by_type

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _format_checklist(checklist: List[Dict[str, Any]]) -> str:
    """格式化检查清单，用于显示"""
    if not checklist:
        return "无检查项"

    result = ""
    for item in checklist:
        if isinstance(item, dict):
            item_id = item.get("id", "")
            item_name = item.get("name", item_id)
            result += f"\n  - {item_name}"
        else:
            result += f"\n  - {item}"

    return result


def _format_deliverables(deliverables: List[Dict[str, Any]]) -> str:
    """格式化交付物，用于显示"""
    if not deliverables:
        return "无交付物"

    result = ""
    for item in deliverables:
        if isinstance(item, dict):
            item_id = item.get("id", "")
            item_name = item.get("name", item_id)
            result += f"\n  - {item_name}"
        else:
            result += f"\n  - {item}"

    return result


def create_workflow_from_rule(rule_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    从规则文件创建工作流

    Args:
        rule_path: 规则文件路径
        output_path: 输出文件路径，不提供则自动生成

    Returns:
        工作流定义
    """
    # 解析规则
    rule_parser = RuleParser()
    rule_data = rule_parser.parse_rule_file(rule_path)

    if not rule_data:
        logger.error(f"解析规则文件失败: {rule_path}")
        return {}

    # 转换为工作流
    converter = FlowConverter()
    workflow = converter.convert_rule_to_workflow(rule_data)

    # 保存工作流定义
    if workflow:
        exporter = JsonExporter()
        exporter.export_workflow(workflow, output_path)

        logger.info(f"已从规则创建工作流: {workflow.get('id')}")

        # 输出Mermaid图
        mermaid_exporter = MermaidExporter()
        mermaid_code = mermaid_exporter.export_workflow(workflow)
        logger.info(f"工作流Mermaid图:\n{mermaid_code}")

    return workflow


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
                            stage_manager.add_completed_item(stage_instance.id, item_id)

                    # 获取阶段进度信息
                    progress_info = stage_manager.get_instance_progress(stage_instance.id)

                    # 创建阶段实例ID
                    stage_instance_id = stage_instance.id
                except ValueError as e:
                    logger.error(f"创建阶段实例失败: {str(e)}")
                    return False, f"创建阶段实例失败: {str(e)}", None
            else:
                # 创建一个新的工作流会话
                workflow_id = workflow.get("id")
                session_name = instance_name or f"{workflow_name}-{stage_name}"

                session_manager = FlowSessionManager(db_session)
                try:
                    # 创建会话
                    flow_session = session_manager.create_session(workflow_id, session_name)
                    session_id = flow_session.id

                    # 创建并启动阶段实例
                    stage_manager = StageInstanceManager(db_session)
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
                            stage_manager.add_completed_item(stage_instance.id, item_id)

                    # 获取阶段进度信息
                    progress_info = stage_manager.get_instance_progress(stage_instance.id)

                    # 创建阶段实例ID
                    stage_instance_id = stage_instance.id
                except ValueError as e:
                    logger.error(f"创建会话失败: {str(e)}")
                    return False, f"创建会话失败: {str(e)}", None

            # 创建上下文数据
            context_data = {
                "workflow_id": workflow.get("id"),
                "workflow_name": workflow.get("name"),
                "stage_id": stage_info.get("id"),
                "stage_name": stage_info.get("name"),
                "session_id": session_id,  # 添加会话ID到上下文
                "stage_instance_id": stage_instance_id,  # 添加阶段实例ID到上下文
                "instance_name": stage_instance.name,
                "checklist": stage_info.get("checklist", []),
                "completed_items": completed_items or [],
                "deliverables": stage_info.get("deliverables", []),
                "description": stage_info.get("description", ""),
            }

            # 获取完整的上下文
            context_provider = ContextProvider()
            full_context = context_provider.provide_context_to_agent(
                workflow.get("id"),
                {
                    "current_stage": stage_info.get("id"),
                    "completed_items": completed_items or [],
                    "session_id": session_id,  # 添加会话ID到上下文提供器
                    "stage_instance_id": stage_instance_id,  # 添加阶段实例ID到上下文提供器
                },
            )

            if full_context:
                context_data["full_context"] = full_context

            # 设置当前会话的当前阶段
            session_manager.set_current_stage(session_id, stage_info.get("id"))

            # 生成好看的输出消息
            output_message = f"""✅ 已启动 {workflow_name} 工作流的 {stage_name} 阶段

- 阶段ID: {stage_instance_id}
- 名称: {stage_instance.name}
- 描述: {stage_info.get('description', '未提供描述')}

📋 检查清单:
{_format_checklist(stage_info.get('checklist', []))}

📦 交付物:
{_format_deliverables(stage_info.get('deliverables', []))}

⏭️ 可以使用以下命令获取上下文:
vc flow context {workflow.get('id')} --stage={stage_info.get('id')}
"""

            return True, output_message, context_data

    except Exception as e:
        logger.exception(f"处理工作流阶段执行请求时出错: {workflow_name}:{stage_name}")
        return False, f"处理工作流阶段执行请求时出错: {str(e)}", None


def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(description="VibeCopilot工作流命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 创建工作流
    create_parser = subparsers.add_parser("create", help="从规则创建工作流")
    create_parser.add_argument("rule_path", help="规则文件路径")
    create_parser.add_argument("--output", "-o", help="输出文件路径")

    # 导出工作流
    export_parser = subparsers.add_parser("export", help="导出工作流")
    export_parser.add_argument("workflow_id", help="工作流ID")
    export_parser.add_argument(
        "--format", "-f", choices=["json", "mermaid"], default="json", help="导出格式"
    )
    export_parser.add_argument("--output", "-o", help="输出文件路径")

    # 获取上下文
    context_parser = subparsers.add_parser("context", help="获取工作流上下文")
    context_parser.add_argument("workflow_id", help="工作流ID")
    context_parser.add_argument("--stage", "-s", help="当前阶段ID")
    context_parser.add_argument("--completed", "-c", nargs="*", help="已完成的检查项")

    # 列出工作流
    subparsers.add_parser("list", help="列出所有工作流")

    # 运行工作流阶段
    run_parser = subparsers.add_parser("run", help="运行工作流特定阶段")
    run_parser.add_argument("workflow_stage", help="工作流阶段，格式为workflow_name:stage_name")
    run_parser.add_argument("--name", "-n", help="阶段实例名称")
    run_parser.add_argument("--completed", "-c", nargs="*", help="已完成的检查项")
    run_parser.add_argument("--session", "-s", help="会话ID，指定以使用现有会话")

    # 注册流会话子命令
    # 流会话子命令通过flow_session包中的register_commands函数添加
    # 导入并注册会话命令
    from src.flow_session import register_commands

    register_commands(subparsers)

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 处理命令
    if args.command == "create":
        create_workflow_from_rule(args.rule_path, args.output)

    elif args.command == "export":
        exporter = JsonExporter()
        workflow = exporter.load_workflow(args.workflow_id)

        if not workflow:
            logger.error(f"找不到工作流: {args.workflow_id}")
            return

        if args.format == "json":
            output_path = args.output or f"{args.workflow_id}.json"
            exporter.export_workflow(workflow, output_path)
            logger.info(f"已导出工作流到: {output_path}")

        elif args.format == "mermaid":
            mermaid_exporter = MermaidExporter()
            mermaid_code = mermaid_exporter.export_workflow(workflow)

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(mermaid_code)
                logger.info(f"已导出Mermaid图到: {args.output}")
            else:
                print(mermaid_code)

    elif args.command == "context":
        progress_data = {"current_stage": args.stage, "completed_items": args.completed or []}

        context = get_workflow_context(args.workflow_id, progress_data)
        print(json.dumps(context, ensure_ascii=False, indent=2))

    elif args.command == "list":
        exporter = JsonExporter()
        workflows = exporter.list_workflows()

        if not workflows:
            logger.info("没有找到工作流")
            return

        print(f"找到 {len(workflows)} 个工作流:")
        for workflow in workflows:
            print(f"  - {workflow['id']}: {workflow['name']}")
            print(f"    描述: {workflow['description']}")
            print(f"    来源: {workflow['source_rule']}")
            print()

    elif args.command == "run":
        if not args.workflow_stage or ":" not in args.workflow_stage:
            logger.error("工作流阶段格式错误，应为workflow_name:stage_name")
            return

        workflow_name, stage_name = args.workflow_stage.split(":", 1)
        success, message, context = run_workflow_stage(
            workflow_name, stage_name, args.name, args.completed, args.session
        )

        print(message)
        if success:
            logger.info(f"成功运行工作流阶段: {args.workflow_stage}")
        else:
            logger.error(f"运行工作流阶段失败: {args.workflow_stage}")


if __name__ == "__main__":
    main()
