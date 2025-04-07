"""
Flow 'create' subcommand handler.
"""
import json
import logging
import os
from typing import Any, Dict

from src.workflow.flow_cmd.workflow_creator import create_workflow_from_rule, create_workflow_from_template_with_vars

logger = logging.getLogger(__name__)


def handle_create_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理创建子命令

    Args:
        args: 命令参数

    Returns:
        命令结果
    """
    result = {
        "status": "error",
        "code": 1,
        "message": "",
        "data": None,
        "meta": {"command": "flow create", "args": args},
    }

    # 获取参数
    rule_path = args.get("rule_path")
    template_name = args.get("template")
    output_path = args.get("output")
    variables_file = args.get("variables")

    # 检查参数
    if not rule_path and not template_name:
        result["message"] = "必须提供规则文件路径或模板名称"
        result["code"] = 400
        return result

    # 如果提供了规则文件路径，从规则创建工作流
    if rule_path:
        try:
            if not os.path.exists(rule_path):
                result["message"] = f"规则文件不存在: {rule_path}"
                result["code"] = 404
                return result

            workflow = create_workflow_from_rule(rule_path, output_path)
            if not workflow:
                result["message"] = f"从规则创建工作流失败: {rule_path}"
                return result

            result["status"] = "success"
            result["code"] = 0
            result["data"] = {
                "workflow_id": workflow.get("id"),
                "workflow_name": workflow.get("name"),
                "workflow": workflow,
            }
            result["message"] = f"成功创建工作流: {workflow.get('name')}"
            return result
        except Exception as e:
            logger.error(f"从规则创建工作流时出错: {str(e)}", exc_info=True)
            result["message"] = f"从规则创建工作流时出错: {str(e)}"
            result["code"] = 500
            return result

    # 如果提供了模板名称，从模板创建工作流
    elif template_name:
        try:
            # 加载变量
            variables = {}
            if variables_file and os.path.exists(variables_file):
                try:
                    with open(variables_file, "r", encoding="utf-8") as f:
                        variables = json.load(f)
                except json.JSONDecodeError as json_e:
                    result["message"] = f"解析变量文件失败 ({variables_file}): {json_e}"
                    result["code"] = 400
                    return result
                except Exception as read_e:
                    result["message"] = f"读取变量文件失败 ({variables_file}): {read_e}"
                    result["code"] = 500
                    return result

            workflow = create_workflow_from_template_with_vars(template_name, variables, output_path)
            if not workflow:
                result["message"] = f"从模板创建工作流失败: {template_name}"
                return result

            result["status"] = "success"
            result["code"] = 0
            result["data"] = {
                "workflow_id": workflow.get("id"),
                "workflow_name": workflow.get("name"),
                "workflow": workflow,
            }
            result["message"] = f"成功创建工作流: {workflow.get('name')}"
            return result
        except Exception as e:
            logger.error(f"从模板创建工作流时出错: {str(e)}", exc_info=True)
            result["message"] = f"从模板创建工作流时出错: {str(e)}"
            result["code"] = 500
            return result

    # Should not be reached if logic is correct
    result["message"] = "未知的创建流程错误"
    return result
