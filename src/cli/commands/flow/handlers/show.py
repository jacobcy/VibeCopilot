"""
Flow 'show' subcommand handler.
"""
import json
import logging
from typing import Any, Dict, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from sqlalchemy.orm import Session

from src.cli.commands.flow.handlers.formatter import format_session_summary, format_stage_summary, format_workflow_summary
from src.cli.commands.flow.handlers.visualize import generate_session_mermaid, generate_workflow_mermaid
from src.db import get_session_factory
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
from src.flow_session.manager import get_session
from src.utils.id_generator import EntityType, IdGenerator
from src.workflow.service import get_workflow, get_workflow_by_name, get_workflow_by_type
from src.workflow.utils import MermaidExporter

# Assuming these helpers and operations are accessible
from src.workflow.utils.helpers import format_checklist, format_deliverables, format_workflow_stages

logger = logging.getLogger(__name__)
console = Console()


def _parse_workflow_structure(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
    """解析工作流数据，提取阶段和转换"""
    structure = {"stages": [], "transitions": []}

    # 首先检查是否有直接的stages和transitions字段
    if "stages" in workflow_data and isinstance(workflow_data["stages"], list):
        logger.debug(f"Found direct 'stages' field with {len(workflow_data['stages'])} items")
        # 直接使用stages字段
        for stage in workflow_data["stages"]:
            if isinstance(stage, dict):
                stage_info = {
                    "id": stage.get("id", "unknown_stage"),
                    "name": stage.get("name", "Unknown Stage"),
                    "description": stage.get("description", ""),
                }
                structure["stages"].append(stage_info)

        # 直接使用transitions字段
        if "transitions" in workflow_data and isinstance(workflow_data["transitions"], list):
            logger.debug(f"Found direct 'transitions' field with {len(workflow_data['transitions'])} items")
            for transition in workflow_data["transitions"]:
                if isinstance(transition, dict):
                    transition_info = {
                        "from": transition.get("from_stage", transition.get("from", "unknown")),
                        "to": transition.get("to_stage", transition.get("to", "unknown")),
                        "condition": transition.get("condition", ""),
                    }
                    structure["transitions"].append(transition_info)

        # 如果有直接的stages和transitions，直接返回
        if structure["stages"]:
            logger.debug(f"Using direct stages/transitions fields: {len(structure['stages'])} stages, {len(structure['transitions'])} transitions")
            return structure

    # 如果没有直接的字段，尝试从 stages_data 中获取
    stages_data_raw = workflow_data.get("stages_data")
    logger.debug(f"Raw stages_data received: Type={type(stages_data_raw)}, Snippet={str(stages_data_raw)[:200]}...")

    if stages_data_raw is None:
        logger.warning(f"No stages_data found in workflow {workflow_data.get('id')}")
        return structure

    # 如果 stages_data 是字典，尝试从字典中获取 stages 和 transitions
    if isinstance(stages_data_raw, dict):
        logger.debug(f"stages_data is a dictionary with keys: {list(stages_data_raw.keys())}")

        # 尝试从字典中获取 stages
        stages_list = stages_data_raw.get("stages", [])
        if isinstance(stages_list, list):
            logger.debug(f"Found stages list in stages_data with {len(stages_list)} items")
            for stage in stages_list:
                if isinstance(stage, dict):
                    stage_info = {
                        "id": stage.get("id", "unknown_stage"),
                        "name": stage.get("name", "Unknown Stage"),
                        "description": stage.get("description", ""),
                    }
                    structure["stages"].append(stage_info)

        # 尝试从字典中获取 transitions
        transitions_list = stages_data_raw.get("transitions", [])
        if isinstance(transitions_list, list):
            logger.debug(f"Found transitions list in stages_data with {len(transitions_list)} items")
            for transition in transitions_list:
                if isinstance(transition, dict):
                    transition_info = {
                        "from": transition.get("from_stage", transition.get("from", "unknown")),
                        "to": transition.get("to_stage", transition.get("to", "unknown")),
                        "condition": transition.get("condition", ""),
                    }
                    structure["transitions"].append(transition_info)

        # 如果从字典中找到了 stages，返回结果
        if structure["stages"]:
            logger.debug(
                f"Using stages/transitions from stages_data dictionary: {len(structure['stages'])} stages, {len(structure['transitions'])} transitions"
            )
            return structure

    # 如果 stages_data 是列表，尝试将其解析为阶段列表
    if isinstance(stages_data_raw, list):
        logger.debug(f"stages_data is a list with {len(stages_data_raw)} items")
        stages_data = stages_data_raw
    elif isinstance(stages_data_raw, str):
        # 尝试解析JSON字符串
        try:
            parsed = json.loads(stages_data_raw)
            if isinstance(parsed, list):
                stages_data = parsed
                logger.debug("Successfully parsed stages_data string into a list.")
            elif isinstance(parsed, dict) and "stages" in parsed:
                # 如果解析出来的是字典，尝试获取 stages 字段
                stages_data = parsed.get("stages", [])
                logger.debug(f"Extracted stages list from parsed dictionary, found {len(stages_data)} items")
            else:
                logger.error(f"Parsed stages_data is not a list or valid dictionary. Type: {type(parsed)}")
                return structure
        except json.JSONDecodeError as e:
            logger.error(f"Workflow {workflow_data.get('id')} stages_data is an invalid JSON string: {e}")
            return structure
    else:
        logger.error(f"Workflow {workflow_data.get('id')} stages_data has unsupported type: {type(stages_data_raw)}")
        return structure

    # 处理阶段列表
    valid_stages_for_transitions = []
    for idx, stage_raw in enumerate(stages_data):
        if isinstance(stage_raw, dict):
            stage_info = {
                "id": stage_raw.get("id", f"unknown_stage_{idx}"),
                "name": stage_raw.get("name", f"Unknown Stage {idx}"),
                "description": stage_raw.get("description", ""),
            }
            structure["stages"].append(stage_info)
            valid_stages_for_transitions.append(stage_info)
        else:
            logger.warning(f"Invalid stage data format at index {idx}. Expected dict, got {type(stage_raw)}.")

    # 如果没有显式的转换，则从阶段顺序推断
    if not structure["transitions"] and len(valid_stages_for_transitions) > 1:
        logger.debug(f"No explicit transitions found, inferring from {len(valid_stages_for_transitions)} stages")
        for i in range(len(valid_stages_for_transitions) - 1):
            from_stage = valid_stages_for_transitions[i]
            to_stage = valid_stages_for_transitions[i + 1]
            transition_info = {"from": from_stage["id"], "to": to_stage["id"], "condition": "(Inferred from order of stages)"}
            structure["transitions"].append(transition_info)

    logger.debug(f"Final structure: {len(structure['stages'])} stages, {len(structure['transitions'])} transitions")
    return structure


def _format_workflow_yaml(workflow_data: Dict[str, Any], structure: Dict[str, Any]) -> str:
    """将工作流数据和解析后的结构格式化为YAML字符串"""
    # Log the structure received by the formatter
    logger.debug(f"_format_workflow_yaml received structure: {json.dumps(structure, indent=2)}")

    yaml_output_lines = []
    yaml_output_lines.append(f"workflow:")
    yaml_output_lines.append(f"  id: {workflow_data.get('id', 'N/A')}")
    yaml_output_lines.append(f"  name: {workflow_data.get('name', 'N/A')}")

    description = workflow_data.get("description", "")
    if "\n" in description:
        yaml_output_lines.append(f"  description: |")
        for line in description.split("\n"):
            yaml_output_lines.append(f"    {line}")
    else:
        yaml_output_lines.append(f"  description: {description}")

    if structure["stages"]:
        yaml_output_lines.append("  stages:")
        for stage in structure["stages"]:
            yaml_output_lines.append(f"    - id: {stage['id']}")
            yaml_output_lines.append(f"      name: {stage['name']}")
            stage_desc = stage["description"]
            if "\n" in stage_desc:
                yaml_output_lines.append(f"      description: |")
                for line in stage_desc.split("\n"):
                    yaml_output_lines.append(f"        {line}")
            else:
                yaml_output_lines.append(f"      description: {stage_desc}")
    else:
        yaml_output_lines.append("  stages: []")

    if structure["transitions"]:
        yaml_output_lines.append("  transitions:")
        for trans in structure["transitions"]:
            yaml_output_lines.append(f"    - from: {trans['from']}")
            yaml_output_lines.append(f"      to: {trans['to']}")
            yaml_output_lines.append(f"      condition: {trans['condition']}")
    else:
        yaml_output_lines.append("  transitions: []")

    return "\n".join(yaml_output_lines)


def handle_show_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理显示工作流或会话详情的子命令

    Args:
        args: 命令参数
            - id: 工作流或会话ID/名称 (可选，默认当前会话)
            - format: 输出格式 ('json', 'text', 'mermaid')
            - diagram: 是否包含Mermaid图表
            - verbose: 是否显示详细信息

    Returns:
        命令结果字典
    """
    target_id_or_name = args.get("id")
    output_format = args.get("format", "yaml")
    include_diagram = args.get("diagram", False)
    verbose = args.get("verbose", False)

    is_workflow = False
    target_id_to_use = target_id_or_name

    # Determine entity type based on ID prefix
    if target_id_or_name:
        entity_type = IdGenerator.get_entity_type_from_id(target_id_or_name)
        if entity_type == EntityType.WORKFLOW:
            is_workflow = True
            logger.info(f"Detected workflow ID: {target_id_or_name}")
        elif entity_type == EntityType.SESSION:
            is_workflow = False
            logger.info(f"Detected session ID: {target_id_or_name}")
        else:
            is_workflow = False
            logger.info(f"No standard prefix found for '{target_id_or_name}', assuming session ID or name.")
    else:
        is_workflow = False
        logger.info("No ID provided, defaulting to current session.")

    try:
        if is_workflow:
            # --- Show Workflow Definition ---
            if not target_id_to_use:
                return _create_error_response("查看工作流定义时必须提供ID", 400, args)

            # Get the workflow object (might be ORM object)
            workflow_obj = get_workflow(target_id_to_use)
            if not workflow_obj:
                return _create_error_response(f"找不到工作流: {target_id_to_use}", 404, args)

            # Ensure we have a dictionary to work with
            if hasattr(workflow_obj, "to_dict"):
                workflow_data = workflow_obj.to_dict()
            elif isinstance(workflow_obj, dict):
                workflow_data = workflow_obj
            else:
                logger.error(f"get_workflow returned unexpected type: {type(workflow_obj)}")
                return _create_error_response(f"无法处理工作流数据格式", 500, args)

            # Parse structure once using the dictionary
            structure = _parse_workflow_structure(workflow_data)
            mermaid_code = ""
            if output_format == "mermaid" or include_diagram:
                try:
                    exporter = MermaidExporter()
                    # Pass the dictionary to the exporter
                    mermaid_code = exporter.export_workflow(workflow_data)
                except Exception as e:
                    logger.warning(f"无法生成工作流 {target_id_to_use} 的Mermaid图: {e}")
                    mermaid_code = f"# Error generating diagram: {e}"

            if output_format == "json":
                if include_diagram:
                    # Add diagram to the dict before dumping
                    workflow_data["diagram_mermaid"] = mermaid_code
                return {
                    "status": "success",
                    "code": 0,
                    # Dump the dictionary, not the original object
                    "message": json.dumps(workflow_data, ensure_ascii=False, indent=2),
                    "data": workflow_data,
                    "meta": {"command": "flow show", "args": args},
                }
            elif output_format == "mermaid":
                return {
                    "status": "success",
                    "code": 0,
                    "message": mermaid_code,
                    "data": {"mermaid_code": mermaid_code},
                    "meta": {"command": "flow show", "args": args},
                }
            elif output_format == "text":  # Keep explicit text option for summary
                # Pass the dictionary to the formatter
                workflow_summary = format_workflow_summary(workflow_data)
                output = workflow_summary
                if include_diagram:
                    # Append raw diagram for text format too
                    output += f"\n\n---\nDiagram (Mermaid):\n```mermaid\n{mermaid_code}\n```"
                return {
                    "status": "success",
                    "code": 0,
                    "message": output,
                    "data": workflow_data,
                    "meta": {"command": "flow show", "args": args},
                }
            else:  # Default is 'yaml'
                # Pass the dictionary to the formatter
                yaml_message = _format_workflow_yaml(workflow_data, structure)
                if include_diagram:
                    # Append raw mermaid code after YAML content, separated
                    yaml_message += f"\n\n---\nDiagram (Mermaid):\n```mermaid\n{mermaid_code}\n```"  # Remove the commenting and replace logic
                return {
                    "status": "success",
                    "code": 0,
                    "message": yaml_message,
                    "data": workflow_data,  # Return dict data
                    "meta": {"command": "flow show", "args": args},
                }

        else:
            # --- Show Session --- (Default behavior)
            session_obj = get_session(target_id_to_use)
            if not session_obj:
                # Error message is handled by get_session_by_id_or_name_or_current
                # Update error message slightly as get_session might not print verbose info directly
                error_message = f"找不到会话: {target_id_to_use if target_id_to_use else '当前活动会话'}"
                logger.warning(error_message)
                return _create_error_response(error_message, 404, args)

            # Convert SQLAlchemy object to dict for consistent handling
            session_dict = session_obj.to_dict()

            if output_format == "json":
                return {
                    "status": "success",
                    "code": 0,
                    "message": json.dumps(session_dict, ensure_ascii=False, indent=2),
                    "data": session_dict,
                    "meta": {"command": "flow show", "args": args},
                }
            elif output_format == "mermaid":
                # Mermaid format doesn't make sense for a session, return error or text?
                # Returning text format seems more user-friendly than an error.
                logger.warning("Mermaid format is not applicable for sessions. Returning text format instead.")
                session_summary = format_session_summary(session_dict, verbose)
                return {
                    "status": "success",
                    "code": 0,
                    "message": session_summary,
                    "data": session_dict,
                    "meta": {"command": "flow show", "args": args},
                }
            else:  # Default to text format
                session_summary = format_session_summary(session_dict, verbose)
                return {
                    "status": "success",
                    "code": 0,
                    "message": session_summary,
                    "data": session_dict,
                    "meta": {"command": "flow show", "args": args},
                }

    except Exception as e:
        logger.error(f"获取详情时出错 ({'工作流' if is_workflow else '会话'} ID/名称: {target_id_to_use}): {str(e)}", exc_info=True)
        return _create_error_response(f"处理请求时发生意外错误: {str(e)}", 500, args)


def _create_error_response(message: str, code: int, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建统一的错误响应

    Args:
        message: 错误消息
        code: 错误代码
        args: 原始命令参数

    Returns:
        错误响应字典
    """
    return {
        "status": "error",
        "code": code,
        "message": message,
        "data": None,
        "meta": {"command": "flow show", "args": args},
    }
