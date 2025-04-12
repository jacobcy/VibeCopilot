"""
Flow 'import' subcommand handler.
"""
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel

from src.utils.file_utils import ensure_directory_exists, file_exists, read_json_file, write_json_file
from src.validation.core.workflow_validator import WorkflowValidator
from src.workflow.workflow_operations import ensure_directory_exists, get_workflows_directory, list_workflows, write_json_file

logger = logging.getLogger(__name__)
console = Console()


def handle_import_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理导入工作流子命令

    导入(import)与创建(create)的区别：
    - 导入直接复制已有工作流文件，只进行基本验证
    - 创建需要从规则或模板解析生成新工作流

    Args:
        args: 命令参数 (来自 argparse)
            - file_path: 要导入的工作流文件路径
            - name: 可选，导入后使用的工作流名称，如不提供则使用原名称

    Returns:
        命令结果字典
    """
    file_path = args.get("file_path")
    new_name = args.get("name")  # 获取可能提供的新名称

    if not file_path:
        logger.error("未提供工作流文件路径")
        return {
            "status": "error",
            "code": 400,
            "message": "未提供工作流文件路径",
            "data": None,
            "meta": {"command": "flow import", "args": args},
        }

    try:
        # 检查文件是否存在
        if not file_exists(file_path):
            logger.error(f"工作流文件不存在: {file_path}")
            return {
                "status": "error",
                "code": 404,
                "message": f"工作流文件不存在: {file_path}",
                "data": None,
                "meta": {"command": "flow import", "args": args},
            }

        # 读取工作流文件
        logger.info(f"正在从 {file_path} 导入工作流...")
        workflow_data = read_json_file(file_path)

        if not workflow_data:
            logger.error(f"工作流文件为空或格式不正确: {file_path}")
            return {
                "status": "error",
                "code": 400,
                "message": f"工作流文件为空或格式不正确: {file_path}",
                "data": None,
                "meta": {"command": "flow import", "args": args},
            }

        # 获取工作流名称
        original_name = workflow_data.get("name")
        if not original_name:
            logger.error(f"工作流数据缺少必要字段(name): {file_path}")
            return {
                "status": "error",
                "code": 400,
                "message": f"工作流数据缺少必要字段(name): {file_path}",
                "data": None,
                "meta": {"command": "flow import", "args": args},
            }

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
            return {
                "status": "error",
                "code": 400,
                "message": error_msg,
                "data": None,
                "meta": {"command": "flow import", "args": args},
            }

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
            console.print(f"[yellow]替换已存在的同名工作流: {workflow_name}[/yellow]")
        else:
            workflow_data["metadata"]["created_at"] = current_time
            workflow_data["metadata"]["updated_at"] = current_time

        # 保存工作流
        if write_json_file(target_path, workflow_data):
            name_change_info = f" (原名称: {original_name})" if new_name else ""
            success_msg = f"成功导入工作流: {workflow_name}{name_change_info} (ID: {new_workflow_id})"
            logger.info(success_msg)
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
            return {
                "status": "error",
                "code": 500,
                "message": error_msg,
                "data": None,
                "meta": {"command": "flow import", "args": args},
            }

    except Exception as e:
        error_msg = f"导入工作流时出错: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "code": 500,
            "message": error_msg,
            "data": None,
            "meta": {"command": "flow import", "args": args},
        }
