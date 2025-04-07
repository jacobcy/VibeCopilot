"""
Flow 'export' subcommand handler.
"""
import logging
import os
from typing import Any, Dict

# Assuming exporters and workflow_operations are accessible
from src.workflow.exporters.json_exporter import JsonExporter
from src.workflow.exporters.mermaid_exporter import MermaidExporter
from src.workflow.workflow_operations import get_workflow_by_type  # Keep if needed
from src.workflow.workflow_operations import get_workflow

logger = logging.getLogger(__name__)


def handle_export_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理导出子命令

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
        "meta": {"command": "flow export", "args": args},
    }

    try:
        # 获取参数
        workflow_id_or_type = args.get("workflow_id")  # Can be ID or Type
        output_path = args.get("output")
        format_type = args.get("format", "json")  # Default to json

        # 检查参数
        if not workflow_id_or_type:
            result["message"] = "必须提供工作流ID或类型"
            result["code"] = 400
            return result

        # 获取工作流定义 (Adjust based on how definitions are stored/retrieved)
        workflow = get_workflow(workflow_id_or_type)
        if not workflow:
            result["message"] = f"找不到工作流: {workflow_id_or_type}"
            result["code"] = 404
            return result

        workflow_data = workflow  # Assume it's a dict or similar

        # 根据格式导出
        if format_type.lower() == "json":
            exporter = JsonExporter()
            # Exporter should handle writing to file or returning content
            export_content = exporter.export_workflow_to_string(workflow_data)
            if output_path:
                try:
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(export_content)
                    result["status"] = "success"
                    result["code"] = 0
                    result["message"] = f"已将工作流导出为JSON: {output_path}"
                    result["data"] = {"file_path": output_path}
                except Exception as write_e:
                    logger.error(f"写入导出的 JSON 文件时出错 ({output_path}): {write_e}", exc_info=True)
                    result["message"] = f"写入导出文件失败: {write_e}"
                    result["code"] = 500
            else:
                # Return JSON content in data
                result["status"] = "success"
                result["code"] = 0
                result["message"] = "工作流定义 (JSON)"
                result["data"] = {"json_content": export_content}
            return result

        elif format_type.lower() == "mermaid":
            try:
                exporter = MermaidExporter()
                mermaid_code = exporter.export_workflow(workflow_data)
            except Exception as mermaid_e:
                logger.error(f"生成 Mermaid 图表时出错: {mermaid_e}", exc_info=True)
                result["message"] = f"生成 Mermaid 图表失败: {mermaid_e}"
                result["code"] = 500
                return result

            if output_path:
                # 保存到文件
                try:
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(mermaid_code)
                    result["status"] = "success"
                    result["code"] = 0
                    result["message"] = f"已将工作流导出为Mermaid: {output_path}"
                    result["data"] = {"file_path": output_path}
                except Exception as write_e:
                    logger.error(f"写入导出的 Mermaid 文件时出错 ({output_path}): {write_e}", exc_info=True)
                    result["message"] = f"写入导出文件失败: {write_e}"
                    result["code"] = 500
            else:
                # 直接返回代码
                result["status"] = "success"
                result["code"] = 0
                result["message"] = "工作流图表 (Mermaid)"
                result["data"] = {"mermaid_code": mermaid_code}

            return result

        else:
            result["message"] = f"不支持的导出格式: {format_type}"
            result["code"] = 400
            return result

    except Exception as e:
        logger.error(f"导出工作流时出错: {str(e)}", exc_info=True)
        result["message"] = f"导出工作流时出错: {str(e)}"
        result["code"] = 500
        result["data"] = None  # Ensure data is None on error
        return result
