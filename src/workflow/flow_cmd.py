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
from typing import Any, Dict, List, Optional

from src.workflow.exporters.json_exporter import JsonExporter
from src.workflow.exporters.mermaid_exporter import MermaidExporter
from src.workflow.interpreter.context_provider import ContextProvider
from src.workflow.interpreter.flow_converter import FlowConverter
from src.workflow.interpreter.rule_parser import RuleParser

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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


if __name__ == "__main__":
    main()
