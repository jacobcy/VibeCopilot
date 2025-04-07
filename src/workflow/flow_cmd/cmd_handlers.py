"""
工作流命令处理器模块

提供各种子命令的处理功能
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from src.workflow.exporters.json_exporter import JsonExporter
from src.workflow.exporters.mermaid_exporter import MermaidExporter
from src.workflow.flow_cmd.helpers import (
    format_checklist,
    format_deliverables,
    format_workflow_stages,
    format_workflow_steps,
)
from src.workflow.flow_cmd.workflow_creator import (
    create_workflow_from_rule,
    create_workflow_from_template_with_vars,
)
from src.workflow.flow_cmd.workflow_runner import run_workflow_stage
from src.workflow.workflow_operations import (
    get_workflow,
    get_workflow_by_type,
    list_workflows,
    save_workflow,
)

logger = logging.getLogger(__name__)


def handle_create_command(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理创建命令

    Args:
        args: 命令参数

    Returns:
        命令结果
    """
    result = {"success": False, "command": "flow create"}

    # 获取参数
    rule_path = args.get("rule_path")
    template_name = args.get("template")
    output_path = args.get("output")
    variables_file = args.get("variables")

    # 检查参数
    if not rule_path and not template_name:
        result["error"] = "必须提供规则文件路径或模板名称"
        return result

    # 如果提供了规则文件路径，从规则创建工作流
    if rule_path:
        try:
            if not os.path.exists(rule_path):
                result["error"] = f"规则文件不存在: {rule_path}"
                return result

            workflow = create_workflow_from_rule(rule_path, output_path)
            if not workflow:
                result["error"] = f"从规则创建工作流失败: {rule_path}"
                return result

            result["success"] = True
            result["workflow_id"] = workflow.get("id")
            result["workflow_name"] = workflow.get("name")
            result["message"] = f"成功创建工作流: {workflow.get('name')}"
            result["workflow"] = workflow
            return result
        except Exception as e:
            logger.error(f"从规则创建工作流时出错: {str(e)}")
            result["error"] = f"从规则创建工作流时出错: {str(e)}"
            return result

    # 如果提供了模板名称，从模板创建工作流
    elif template_name:
        try:
            # 加载变量
            variables = {}
            if variables_file and os.path.exists(variables_file):
                with open(variables_file, "r") as f:
                    variables = json.load(f)

            workflow = create_workflow_from_template_with_vars(
                template_name, variables, output_path
            )
            if not workflow:
                result["error"] = f"从模板创建工作流失败: {template_name}"
                return result

            result["success"] = True
            result["workflow_id"] = workflow.get("id")
            result["workflow_name"] = workflow.get("name")
            result["message"] = f"成功创建工作流: {workflow.get('name')}"
            result["workflow"] = workflow
            return result
        except Exception as e:
            logger.error(f"从模板创建工作流时出错: {str(e)}")
            result["error"] = f"从模板创建工作流时出错: {str(e)}"
            return result


def handle_list_command(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理列表命令

    Args:
        args: 命令参数

    Returns:
        命令结果
    """
    result = {"success": False, "command": "flow list"}

    try:
        # 获取参数
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")

        # 获取工作流列表
        workflows = list_workflows()

        if not workflows:
            result["success"] = True
            result["message"] = "没有工作流"
            result["workflows"] = []
            return result

        # 处理输出
        if output_format == "json":
            # JSON格式直接返回
            result["success"] = True
            result["message"] = f"共找到 {len(workflows)} 个工作流"
            result["workflows"] = workflows
            return result
        else:
            # 文本格式处理
            workflow_list = []
            for workflow in workflows:
                info = f"{workflow.get('id')}: {workflow.get('name')}"
                if verbose:
                    # 添加描述
                    description = workflow.get("description", "无描述")
                    info += f"\n  描述: {description}"

                    # 添加阶段信息
                    stages = workflow.get("stages", [])
                    if stages:
                        stages_info = format_workflow_stages(stages)
                        info += f"\n  阶段: {stages_info}"

                workflow_list.append(info)

            workflows_text = "\n".join(workflow_list)
            result["success"] = True
            result["message"] = f"共找到 {len(workflows)} 个工作流:\n{workflows_text}"
            result["workflows"] = workflows
            return result
    except Exception as e:
        logger.error(f"获取工作流列表时出错: {str(e)}")
        result["error"] = f"获取工作流列表时出错: {str(e)}"
        return result


def handle_show_command(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理显示命令

    Args:
        args: 命令参数

    Returns:
        命令结果
    """
    result = {"success": False, "command": "flow show"}

    try:
        # 获取参数
        workflow_id = args.get("workflow_id")
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")
        diagram = args.get("diagram", False)

        # 检查参数
        if not workflow_id:
            result["error"] = "必须提供工作流ID"
            return result

        # 获取工作流
        workflow = get_workflow(workflow_id)
        if not workflow:
            # 尝试通过类型获取
            workflow = get_workflow_by_type(workflow_id)

        if not workflow:
            result["error"] = f"找不到工作流: {workflow_id}"
            return result

        # 如果需要生成图表
        if diagram:
            exporter = MermaidExporter()
            mermaid_code = exporter.export_workflow(workflow)
            result["diagram"] = mermaid_code

        # 处理输出
        if output_format == "json":
            # JSON格式直接返回
            result["success"] = True
            result["workflow"] = workflow
            result["message"] = f"工作流ID: {workflow.get('id')}, 名称: {workflow.get('name')}"
            return result
        else:
            # 文本格式处理
            info = f"工作流ID: {workflow.get('id')}\n名称: {workflow.get('name')}"

            # 添加描述
            description = workflow.get("description", "无描述")
            info += f"\n描述: {description}"

            # 添加阶段信息
            stages = workflow.get("stages", [])
            if stages:
                stages_info = format_workflow_stages(stages)
                info += f"\n阶段: {stages_info}"

            # 如果是详细模式，添加更多信息
            if verbose:
                # 添加检查项
                checklist = workflow.get("checklist", [])
                if checklist:
                    checklist_info = format_checklist(checklist)
                    info += f"\n检查项: {checklist_info}"

                # 添加交付物
                deliverables = workflow.get("deliverables", [])
                if deliverables:
                    deliverables_info = format_deliverables(deliverables)
                    info += f"\n交付物: {deliverables_info}"

            result["success"] = True
            result["workflow"] = workflow
            result["message"] = info
            return result
    except Exception as e:
        logger.error(f"显示工作流时出错: {str(e)}")
        result["error"] = f"显示工作流时出错: {str(e)}"
        return result


def handle_run_command(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理运行命令

    Args:
        args: 命令参数

    Returns:
        命令结果
    """
    result = {"success": False, "command": "flow run"}

    try:
        # 获取参数
        workflow_id = args.get("workflow_id")
        stage_id = args.get("stage")
        instance_name = args.get("name")
        session_id = args.get("session")
        completed_items = args.get("completed", [])

        # 检查参数
        if not workflow_id:
            result["error"] = "必须提供工作流ID"
            return result

        if not stage_id:
            result["error"] = "必须提供阶段ID"
            return result

        # 运行工作流阶段
        success, message, data = run_workflow_stage(
            workflow_id, stage_id, instance_name, completed_items, session_id
        )

        result["success"] = success
        if success:
            result["message"] = message
            result["data"] = data
        else:
            result["error"] = message

        return result
    except Exception as e:
        logger.error(f"运行工作流时出错: {str(e)}")
        result["error"] = f"运行工作流时出错: {str(e)}"
        return result


def handle_start_command(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理启动命令

    Args:
        args: 命令参数

    Returns:
        命令结果
    """
    # 启动命令实际上是run命令的特殊情况，只是添加了一些默认参数
    result = {"success": False, "command": "flow start"}

    try:
        # 获取参数
        workflow_type = args.get("workflow_type")
        name = args.get("name")

        # 检查参数
        if not workflow_type:
            result["error"] = "必须提供工作流类型"
            return result

        # 获取工作流
        workflow = get_workflow_by_type(workflow_type)
        if not workflow:
            result["error"] = f"找不到工作流类型: {workflow_type}"
            return result

        # 获取第一个阶段
        stages = workflow.get("stages", [])
        if not stages:
            result["error"] = f"工作流 {workflow_type} 没有定义阶段"
            return result

        first_stage = stages[0]
        stage_id = first_stage.get("id")

        # 构建run命令的参数
        run_args = {
            "workflow_id": workflow_type,
            "stage": stage_id,
            "name": name or f"{workflow_type}_session",
        }

        # 调用run命令
        return handle_run_command(run_args)
    except Exception as e:
        logger.error(f"启动工作流时出错: {str(e)}")
        result["error"] = f"启动工作流时出错: {str(e)}"
        return result


def handle_export_command(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理导出命令

    Args:
        args: 命令参数

    Returns:
        命令结果
    """
    result = {"success": False, "command": "flow export"}

    try:
        # 获取参数
        workflow_id = args.get("workflow_id")
        output_path = args.get("output")
        format_type = args.get("format", "json")

        # 检查参数
        if not workflow_id:
            result["error"] = "必须提供工作流ID"
            return result

        # 获取工作流
        workflow = get_workflow(workflow_id)
        if not workflow:
            # 尝试通过类型获取
            workflow = get_workflow_by_type(workflow_id)

        if not workflow:
            result["error"] = f"找不到工作流: {workflow_id}"
            return result

        # 根据格式导出
        if format_type == "json":
            exporter = JsonExporter()
            file_path = exporter.export_workflow(workflow, output_path)
            result["success"] = True
            result["message"] = f"已将工作流导出为JSON: {file_path}"
            result["file_path"] = file_path
            return result
        elif format_type == "mermaid":
            exporter = MermaidExporter()
            mermaid_code = exporter.export_workflow(workflow)

            if output_path:
                # 保存到文件
                with open(output_path, "w") as f:
                    f.write(mermaid_code)
                result["success"] = True
                result["message"] = f"已将工作流导出为Mermaid: {output_path}"
                result["file_path"] = output_path
            else:
                # 直接返回代码
                result["success"] = True
                result["message"] = "工作流Mermaid图"
                result["mermaid"] = mermaid_code

            return result
        else:
            result["error"] = f"不支持的导出格式: {format_type}"
            return result
    except Exception as e:
        logger.error(f"导出工作流时出错: {str(e)}")
        result["error"] = f"导出工作流时出错: {str(e)}"
        return result
