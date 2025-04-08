"""
Flow 'show' subcommand handler.
"""
import logging
from typing import Any, Dict

from src.workflow import get_workflow, get_workflow_by_type, get_workflow_context  # 直接从workflow包导入

# Assuming these helpers and operations are accessible
from src.workflow.exporters.mermaid_exporter import MermaidExporter
from src.workflow.flow_cmd.helpers import format_checklist, format_deliverables, format_workflow_stages

logger = logging.getLogger(__name__)


def handle_show_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理显示子命令

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
        "meta": {"command": "flow show", "args": args},
    }

    try:
        # 获取参数
        workflow_id_or_type = args.get("workflow_id")  # Can be ID or Type
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")
        diagram = args.get("diagram", False)

        # 检查参数
        if not workflow_id_or_type:
            result["message"] = "必须提供工作流ID或类型"
            result["code"] = 400
            return result

        # 获取工作流 (Adjust based on whether workflows are DB driven)
        # Assume get_workflow tries ID first, then maybe type or uses a unified search
        workflow = get_workflow(workflow_id_or_type)

        if not workflow:
            result["message"] = f"找不到工作流: {workflow_id_or_type}"
            result["code"] = 404
            return result

        workflow_data = workflow  # Assuming get_workflow returns a dict or object with to_dict()
        result["status"] = "success"
        result["code"] = 0
        result["data"] = {"workflow": workflow_data}
        result["message"] = f"工作流ID: {workflow_data.get('id', 'N/A')}, 名称: {workflow_data.get('name', 'Unnamed')}"

        # 如果需要生成图表
        if diagram:
            try:
                exporter = MermaidExporter()
                mermaid_code = exporter.export_workflow(workflow_data)
                result["data"]["diagram"] = mermaid_code  # Add diagram to data payload
                # Message will be updated below if format is text
            except Exception as diag_e:
                logger.error(f"生成工作流图表时出错: {diag_e}", exc_info=True)
                result["data"]["diagram_error"] = str(diag_e)

        # Format for console output if not agent mode and format is text
        if output_format == "text" and not args.get("_agent_mode", False):
            info = f"工作流ID: {workflow_data.get('id', 'N/A')}\n名称: {workflow_data.get('name', 'Unnamed')}"
            description = workflow_data.get("description", "无描述")
            info += f"\n描述: {description}"

            stages = workflow_data.get("stages", [])
            if stages:
                stages_info = format_workflow_stages(stages)
                info += f"\n阶段: {stages_info}"

            if verbose:
                checklist = workflow_data.get("checklist", [])
                if checklist:
                    checklist_info = format_checklist(checklist)
                    info += f"\n检查项: {checklist_info}"
                deliverables = workflow_data.get("deliverables", [])
                if deliverables:
                    deliverables_info = format_deliverables(deliverables)
                    info += f"\n交付物: {deliverables_info}"

            if diagram:
                if result["data"].get("diagram"):
                    info += "\n\n图表 (Mermaid):\n" + result["data"]["diagram"]
                elif result["data"].get("diagram_error"):
                    info += f"\n\n[!] 生成图表失败: {result['data']['diagram_error']}"

            # Override message with formatted text for direct console display
            result["message"] = info
        elif output_format == "mermaid" and result["data"].get("diagram"):
            # If format is mermaid, set message to the diagram code
            result["message"] = result["data"]["diagram"]

        # Ensure diagram isn't duplicated in both message and data for JSON output
        if output_format == "json" and result["data"].get("diagram"):
            pass  # Diagram is already in data

        return result

    except Exception as e:
        logger.error(f"显示工作流时出错: {str(e)}", exc_info=True)
        result["message"] = f"显示工作流时出错: {str(e)}"
        result["code"] = 500
        result["data"] = None  # Ensure data is None on error
        return result
