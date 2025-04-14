"""
工作流创建、更新和删除处理模块
整合了create, delete和update命令的处理逻辑
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from src.utils.file_utils import file_exists, read_json_file, read_text_file
from src.workflow.service import create_workflow, delete_workflow, get_workflows_directory, update_workflow
from src.workflow.utils import create_workflow_from_rule, create_workflow_from_template_with_vars, get_workflow_fuzzy

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
            return _create_error_response(error_msg, 404, args, "flow create")

        # 读取源文件内容
        source_content = read_text_file(source_path)
        if not source_content:
            error_msg = f"源文件为空: {source_path}"
            logger.error(error_msg)
            return _create_error_response(error_msg, 400, args, "flow create")

        # 检查并读取模板
        if not file_exists(template_path):
            error_msg = f"模板文件不存在: {template_path}"
            logger.error(error_msg)
            return _create_error_response(error_msg, 404, args, "flow create")

        template_data = read_json_file(template_path)
        if not template_data:
            error_msg = f"模板文件为空或格式不正确: {template_path}"
            logger.error(error_msg)
            return _create_error_response(error_msg, 400, args, "flow create")

        # 创建规则文件工作流
        # 这里直接调用flow_cmd中的方法，而不是手动创建WorkflowProcessor对象
        if source_path.endswith((".md", ".mdc", ".markdown")):
            created_workflow = await create_workflow_from_rule(source_path)
            if not created_workflow:
                error_msg = "解析源文件失败"
                logger.error(error_msg)
                return _create_error_response(error_msg, 500, args, "flow create")
        else:
            # 准备工作流数据
            workflow_data = {
                "name": workflow_name or os.path.splitext(os.path.basename(source_path))[0],
                "source_file": source_path,
                "template_file": template_path,
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
        return _create_error_response(error_msg, 500, args, "flow create")


def handle_update_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理更新工作流子命令

    Args:
        args: 命令参数
            - id: 工作流ID
            - name: 新的工作流名称(可选)
            - description: 新的工作流描述(可选)
            - verbose: 是否显示详细信息

    Returns:
        命令结果字典
    """
    try:
        workflow_id = args.get("id")
        name = args.get("name")
        description = args.get("description")
        verbose = args.get("verbose", False)

        if not workflow_id:
            error_msg = "缺少必要参数: 工作流ID"
            logger.error(error_msg)
            return _create_error_response(error_msg, 400, args, "flow update")

        # 尝试获取工作流
        workflow = get_workflow_fuzzy(workflow_id)
        if not workflow:
            error_msg = f"未找到ID或名称为 '{workflow_id}' 的工作流"
            logger.error(error_msg)
            return _create_error_response(error_msg, 404, args, "flow update")

        # 获取实际的工作流ID
        actual_id = workflow.get("id")
        workflow_name = workflow.get("name", "未命名工作流")

        if verbose:
            console.print(f"找到工作流: [bold]{workflow_name}[/bold] (ID: {actual_id})")

        # 准备更新数据
        update_data = {}
        if name:
            update_data["name"] = name
        if description:
            update_data["description"] = description

        if not update_data:
            error_msg = "未提供任何更新数据"
            logger.warning(error_msg)
            return {
                "status": "warning",
                "code": 400,
                "message": error_msg,
                "data": None,
                "meta": {"command": "flow update", "args": args},
            }

        # 添加更新时间
        update_data["metadata"] = {"updated_at": datetime.now().isoformat()}

        # 调用flow_cmd模块中的update_workflow函数
        workflows_dir = get_workflows_directory()
        updated_workflow = update_workflow(actual_id, update_data, workflows_dir)

        if updated_workflow:
            updated_items = ", ".join([f"{k}='{v}'" for k, v in update_data.items() if k != "metadata"])
            success_msg = f"成功更新工作流: {workflow_name} (ID: {actual_id}), 更新项: {updated_items}"
            logger.info(success_msg)
            return {
                "status": "success",
                "code": 200,
                "message": success_msg,
                "data": updated_workflow,
                "meta": {"command": "flow update", "args": args},
            }
        else:
            error_msg = f"更新工作流失败: {actual_id}"
            logger.error(error_msg)
            return _create_error_response(error_msg, 500, args, "flow update")

    except Exception as e:
        error_msg = f"更新工作流时出错: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return _create_error_response(error_msg, 500, args, "flow update")


def handle_delete_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理删除工作流子命令

    Args:
        args: 命令参数，包括：
            - workflow_id: 要删除的工作流ID
            - force: 是否强制删除，不提示确认
            - verbose: 是否显示详细信息

    Returns:
        命令结果字典
    """
    try:
        # 获取参数
        workflow_id = args.get("workflow_id")
        force = args.get("force", False)
        verbose = args.get("verbose", False)

        if not workflow_id:
            return _create_error_response("缺少必要参数: workflow_id", 400, args, "flow delete")

        # 尝试找到工作流
        workflow_dir = get_workflows_directory()
        workflow = get_workflow_fuzzy(workflow_id)

        if not workflow:
            return _create_error_response(f"未找到ID或名称为 '{workflow_id}' 的工作流", 404, args, "flow delete")

        # 获取实际的工作流ID
        actual_id = workflow.get("id")
        workflow_name = workflow.get("name", "未命名工作流")

        if verbose:
            console.print(f"找到工作流: [bold]{workflow_name}[/bold] (ID: {actual_id})")

        # 确认删除，除非使用了--force
        confirmed = force
        if not force and not args.get("_agent_mode", False):
            confirmed = Confirm.ask(f"确定要删除工作流 [bold]{workflow_name}[/bold] (ID: {actual_id})?")

        if not confirmed:
            return {
                "status": "cancelled",
                "code": 0,
                "message": "删除操作已取消",
                "data": None,
                "meta": {"command": "flow delete", "args": args},
            }

        # 执行删除
        if delete_workflow(actual_id, workflow_dir):
            return {
                "status": "success",
                "code": 0,
                "message": f"成功删除工作流: {workflow_name} (ID: {actual_id})",
                "data": {"id": actual_id, "name": workflow_name},
                "meta": {"command": "flow delete", "args": args},
            }
        else:
            return _create_error_response(f"删除工作流失败: {actual_id}", 500, args, "flow delete")

    except Exception as e:
        logger.error(f"删除工作流时出错: {str(e)}", exc_info=True)
        return _create_error_response(f"删除工作流时出错: {str(e)}", 500, args, "flow delete")


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
