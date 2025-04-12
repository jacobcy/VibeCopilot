"""
Flow 'create' subcommand handler.
"""
import json
import logging
import os
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel

from src.core.config import get_config
from src.parsing.parsers.openai_parser import OpenAIParser
from src.utils.file_utils import file_exists, read_json_file, read_text_file
from src.workflow.flow_cmd.workflow_creator import create_workflow_from_rule, create_workflow_from_template_with_vars
from src.workflow.workflow_operations import create_workflow

logger = logging.getLogger(__name__)
console = Console()


async def handle_create_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理创建工作流子命令

    Args:
        args: 命令参数
            - source: 源文件路径
            - template: 工作流模板路径
            - name: 工作流名称（可选）
            - output: 输出文件路径（可选）
            - verbose: 是否显示详细信息

    Returns:
        命令结果字典
    """
    try:
        source_path = args.get("source")
        template_path = args.get("template", "templates/flow/default_flow.json")
        workflow_name = args.get("name")
        output_path = args.get("output")
        verbose = args.get("verbose", False)

        # 检查源文件
        if not file_exists(source_path):
            error_msg = f"源文件不存在: {source_path}"
            logger.error(error_msg)
            return {
                "status": "error",
                "code": 404,
                "message": error_msg,
                "data": None,
                "meta": {"command": "flow create", "args": args},
            }

        # 读取源文件内容
        source_content = read_text_file(source_path)
        if not source_content:
            error_msg = f"源文件为空: {source_path}"
            logger.error(error_msg)
            return {
                "status": "error",
                "code": 400,
                "message": error_msg,
                "data": None,
                "meta": {"command": "flow create", "args": args},
            }

        # 检查并读取模板
        if not file_exists(template_path):
            error_msg = f"模板文件不存在: {template_path}"
            logger.error(error_msg)
            return {
                "status": "error",
                "code": 404,
                "message": error_msg,
                "data": None,
                "meta": {"command": "flow create", "args": args},
            }

        template_data = read_json_file(template_path)
        if not template_data:
            error_msg = f"模板文件为空或格式不正确: {template_path}"
            logger.error(error_msg)
            return {
                "status": "error",
                "code": 400,
                "message": error_msg,
                "data": None,
                "meta": {"command": "flow create", "args": args},
            }

        # 使用OpenAI解析源文件内容
        parser = OpenAIParser()
        parser_result = await parser.parse_workflow(source_content, template_data)

        if not parser_result or not parser_result.get("success"):
            error_msg = f"解析源文件失败: {parser_result.get('error', 'OpenAI未返回有效数据')}"
            logger.error(error_msg)
            return {
                "status": "error",
                "code": 500,
                "message": error_msg,
                "data": None,
                "meta": {"command": "flow create", "args": args},
            }

        # 准备工作流数据
        workflow_data = parser_result["content"]

        # 如果指定了名称，覆盖解析结果
        if workflow_name:
            workflow_data["name"] = workflow_name

        # 添加解析数据
        workflow_data["parser_data"] = {
            "source_file": source_path,
            "template_file": template_path,
            "template_info": parser_result.get("template_info", {}),
            "metadata": parser_result.get("metadata", {}),
        }

        # 创建工作流
        output_dir = os.path.dirname(output_path) if output_path else None
        created_workflow = create_workflow(workflow_data, output_dir)

        success_msg = f"成功创建工作流: {created_workflow.get('name')} (ID: {created_workflow.get('id')})"
        logger.info(success_msg)

        if verbose:
            console.print("\n[bold cyan]工作流详情:[/bold cyan]")
            console.print(Panel(json.dumps(created_workflow, indent=2, ensure_ascii=False), title="创建的工作流", border_style="cyan"))

        return {
            "status": "success",
            "code": 200,
            "message": success_msg,
            "data": created_workflow,
            "meta": {"command": "flow create", "args": args},
        }

    except Exception as e:
        error_msg = f"创建工作流失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "code": 500,
            "message": error_msg,
            "data": None,
            "meta": {"command": "flow create", "args": args},
        }
