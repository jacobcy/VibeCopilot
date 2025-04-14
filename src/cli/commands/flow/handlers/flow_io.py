"""
工作流导入导出处理模块
整合了export和import命令的处理逻辑
"""
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from rich.console import Console
from rich.panel import Panel

from src.core.config import get_config
from src.utils.file_utils import ensure_directory_exists, file_exists, read_json_file, write_json_file
from src.validation.core.workflow_validator import WorkflowValidator
from src.workflow.service import get_workflow, get_workflows_directory, list_workflows
from src.workflow.utils import JsonExporter, MermaidExporter

logger = logging.getLogger(__name__)
console = Console()


def handle_export_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理导出工作流子命令

    Args:
        args: 命令参数
            - workflow_id: 工作流ID或类型
            - format: 导出格式 ('json' 或 'mermaid')
            - output: 输出文件路径 (可选)
            - verbose: 是否显示详细信息

    Returns:
        命令结果字典
    """
    try:
        # 获取参数
        workflow_id_or_type = args.get("workflow_id")
        output_path = args.get("output")
        format_type = args.get("format", "json")  # 默认为json
        verbose = args.get("verbose", False)

        # 检查参数
        if not workflow_id_or_type:
            return _create_error_response("必须提供工作流ID或类型", 400, args, "flow export")

        # 获取工作流定义
        workflow = get_workflow(workflow_id_or_type)
        if not workflow:
            return _create_error_response(f"找不到工作流: {workflow_id_or_type}", 404, args, "flow export")

        workflow_data = workflow  # 假设它是dict或类似的

        # 根据格式导出
        if format_type.lower() == "json":
            exporter = JsonExporter()
            # 导出器应处理写入文件或返回内容
            export_content = exporter.export_workflow_to_string(workflow_data)

            if output_path:
                return _export_to_file(export_content, output_path, "JSON", args)
            else:
                # 在data中返回JSON内容
                return {
                    "status": "success",
                    "code": 0,
                    "message": "工作流定义 (JSON)",
                    "data": {"json_content": export_content},
                    "meta": {"command": "flow export", "args": args},
                }

        elif format_type.lower() == "mermaid":
            try:
                exporter = MermaidExporter()
                mermaid_code = exporter.export_workflow(workflow_data)
            except Exception as mermaid_e:
                logger.error(f"生成 Mermaid 图表时出错: {mermaid_e}", exc_info=True)
                return _create_error_response(f"生成 Mermaid 图表失败: {mermaid_e}", 500, args, "flow export")

            if output_path:
                return _export_to_file(mermaid_code, output_path, "Mermaid", args)
            else:
                # 直接返回代码
                return {
                    "status": "success",
                    "code": 0,
                    "message": "工作流图表 (Mermaid)",
                    "data": {"mermaid_code": mermaid_code},
                    "meta": {"command": "flow export", "args": args},
                }

        else:
            return _create_error_response(f"不支持的导出格式: {format_type}", 400, args, "flow export")

    except Exception as e:
        logger.error(f"导出工作流时出错: {str(e)}", exc_info=True)
        return _create_error_response(f"导出工作流时出错: {str(e)}", 500, args, "flow export")


def handle_import_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理导入工作流子命令

    导入(import)与创建(create)的区别：
    - 导入直接复制已有工作流文件，只进行基本验证
    - 创建需要从规则或模板解析生成新工作流

    Args:
        args: 命令参数
            - file_path: 要导入的工作流文件路径
            - name: 可选，导入后使用的工作流名称，如不提供则使用原名称
            - verbose: 是否显示详细信息

    Returns:
        命令结果字典
    """
    file_path = args.get("file_path")
    new_name = args.get("name")  # 获取可能提供的新名称
    verbose = args.get("verbose", False)

    if not file_path:
        logger.error("未提供工作流文件路径")
        return _create_error_response("未提供工作流文件路径", 400, args, "flow import")

    try:
        # 检查文件是否存在
        if not file_exists(file_path):
            logger.error(f"工作流文件不存在: {file_path}")
            return _create_error_response(f"工作流文件不存在: {file_path}", 404, args, "flow import")

        # 读取工作流文件
        logger.info(f"正在从 {file_path} 导入工作流...")
        workflow_data = read_json_file(file_path)

        if not workflow_data:
            logger.error(f"工作流文件为空或格式不正确: {file_path}")
            return _create_error_response(f"工作流文件为空或格式不正确: {file_path}", 400, args, "flow import")

        # 获取工作流名称
        original_name = workflow_data.get("name")
        if not original_name:
            logger.error(f"工作流数据缺少必要字段(name): {file_path}")
            return _create_error_response(f"工作流数据缺少必要字段(name): {file_path}", 400, args, "flow import")

        # 如果提供了新名称，则使用新名称
        if new_name:
            workflow_data["name"] = new_name
            workflow_name = new_name
            logger.info(f"使用新名称: {new_name} (原名称: {original_name})")
        else:
            workflow_name = original_name

        # 验证工作流数据
        validator = WorkflowValidator()
        is_valid, errors = validator.validate_workflow(workflow_data)
        if not is_valid:
            error_msg = "工作流验证失败:\n" + "\n".join(f"  - {error}" for error in errors)
            logger.error(error_msg)
            return _create_error_response(error_msg, 400, args, "flow import")

        # 检查是否存在同名工作流
        existing_workflows = list_workflows()
        existing_workflow = None
        for workflow in existing_workflows:
            if workflow.get("name") == workflow_name:
                existing_workflow = workflow
                break

        # 生成新的工作流ID
        new_workflow_id = str(uuid.uuid4())[:8]  # 使用UUID的前8位作为ID
        workflow_data["id"] = new_workflow_id

        # 导入工作流
        workflows_dir = get_workflows_directory()
        target_path = os.path.join(workflows_dir, f"{new_workflow_id}.json")

        # 确保目录存在
        ensure_directory_exists(workflows_dir)

        # 更新元数据
        current_time = datetime.now().isoformat()

        if "metadata" not in workflow_data:
            workflow_data["metadata"] = {}

        if existing_workflow:
            # 如果存在同名工作流，保留原始创建时间
            if "metadata" in existing_workflow:
                workflow_data["metadata"]["created_at"] = existing_workflow["metadata"].get("created_at", current_time)
            else:
                workflow_data["metadata"]["created_at"] = current_time
            workflow_data["metadata"]["updated_at"] = current_time

            # 删除旧的工作流文件
            old_file = os.path.join(workflows_dir, f"{existing_workflow['id']}.json")
            if os.path.exists(old_file):
                os.remove(old_file)
            logger.info(f"替换已存在的同名工作流: {workflow_name}")
            if verbose:
                console.print(f"[yellow]替换已存在的同名工作流: {workflow_name}[/yellow]")
        else:
            workflow_data["metadata"]["created_at"] = current_time
            workflow_data["metadata"]["updated_at"] = current_time

        # 保存工作流
        if write_json_file(target_path, workflow_data):
            name_change_info = f" (原名称: {original_name})" if new_name else ""
            success_msg = f"成功导入工作流: {workflow_name}{name_change_info} (ID: {new_workflow_id})"
            logger.info(success_msg)

            if verbose:
                console.print(f"[bold green]✓[/bold green] {success_msg}")

                # 显示工作流信息
                console.print("\n[bold cyan]工作流信息:[/bold cyan]")
                console.print(
                    Panel(
                        f"ID: {new_workflow_id}\n"
                        f"名称: {workflow_name}\n"
                        f"描述: {workflow_data.get('description', '无描述')}\n"
                        f"版本: {workflow_data.get('version', '1.0.0')}\n"
                        f"阶段数: {len(workflow_data.get('stages', []))}\n"
                        f"转换数: {len(workflow_data.get('transitions', []))}\n",
                        title="导入的工作流",
                        border_style="cyan",
                    )
                )

            return {
                "status": "success",
                "code": 200,
                "message": success_msg,
                "data": workflow_data,
                "meta": {"command": "flow import", "args": args},
            }
        else:
            error_msg = f"保存工作流文件失败: {target_path}"
            logger.error(error_msg)
            return _create_error_response(error_msg, 500, args, "flow import")

    except Exception as e:
        error_msg = f"导入工作流时出错: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return _create_error_response(error_msg, 500, args, "flow import")


def _export_to_file(content: str, file_path: str, format_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    将内容导出到文件

    Args:
        content: 要导出的内容
        file_path: 输出文件路径
        format_name: 格式名称(用于消息)
        args: 原始参数

    Returns:
        命令结果字典
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "status": "success",
            "code": 0,
            "message": f"已将工作流导出为{format_name}: {file_path}",
            "data": {"file_path": file_path},
            "meta": {"command": "flow export", "args": args},
        }
    except Exception as write_e:
        logger.error(f"写入导出的 {format_name} 文件时出错 ({file_path}): {write_e}", exc_info=True)
        return _create_error_response(f"写入导出文件失败: {write_e}", 500, args, "flow export")


def _create_error_response(message: str, code: int, args: Dict[str, Any], command: str) -> Dict[str, Any]:
    """
    创建统一的错误响应

    Args:
        message: 错误消息
        code: 错误代码
        args: 原始命令参数
        command: 命令名称

    Returns:
        错误响应字典
    """
    return {
        "status": "error",
        "code": code,
        "message": message,
        "data": None,
        "meta": {"command": command, "args": args},
    }
