"""
Flow 'show' subcommand handler.
"""
import json
import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.cli.commands.flow.handlers.formatter import format_stage_summary, format_workflow_summary
from src.cli.commands.flow.handlers.visualize import generate_session_mermaid, generate_workflow_mermaid
from src.db import get_session_factory
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
from src.flow_session.manager import FlowSessionManager
from src.workflow.service import get_workflow, get_workflow_by_name, get_workflow_by_type

# Assuming these helpers and operations are accessible
from src.workflow.utils.helpers import format_checklist, format_deliverables, format_workflow_stages

logger = logging.getLogger(__name__)


def handle_show_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理显示工作流或会话信息的子命令

    根据参数决定显示工作流定义还是会话信息。
    如果args中包含workflow_id和is_workflow=True，则显示工作流定义；
    如果args中包含session_id和is_workflow=False，则显示会话信息。

    Args:
        args: 命令参数
            - id: 工作流ID或会话ID
            - is_workflow: 是否显示工作流定义而非会话
            - format: 输出格式 (json, text, mermaid)
            - diagram: 是否包含图表
            - verbose: 是否显示详细信息

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
        # 获取通用参数
        target_id = args.get("id")  # 此参数可能是工作流ID或会话ID
        is_workflow = args.get("is_workflow", False)  # 默认为显示会话信息
        verbose = args.get("verbose", False)
        output_format = args.get("format", "text")
        diagram = args.get("diagram", False)

        # 检查参数
        if not target_id:
            result["message"] = "必须提供ID参数"
            result["code"] = 400
            return result

        # 根据is_workflow决定展示工作流还是会话
        if is_workflow:
            # 显示工作流定义
            return _show_workflow(target_id, verbose, output_format, diagram, args)
        else:
            # 显示会话信息
            return _show_session(target_id, verbose, output_format, diagram, args)

    except Exception as e:
        logger.error(f"显示信息时出错: {str(e)}", exc_info=True)
        result["message"] = f"显示信息时出错: {str(e)}"
        result["code"] = 500
        result["data"] = None  # Ensure data is None on error
        return result


def _show_workflow(workflow_id: str, verbose: bool, output_format: str, diagram: bool, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    显示工作流定义信息

    Args:
        workflow_id: 工作流ID或名称
        verbose: 是否显示详细信息
        output_format: 输出格式
        diagram: 是否包含图表
        args: 原始命令参数

    Returns:
        命令结果
    """
    result = {
        "status": "error",
        "code": 1,
        "message": "",
        "data": None,
        "meta": {"command": "flow show workflow", "args": args},
    }

    try:
        if verbose:
            logger.debug(f"尝试获取工作流: {workflow_id}")

        # 首先尝试按ID查找
        workflow = get_workflow(workflow_id)

        # 如果未找到，尝试按名称查找
        if not workflow:
            if verbose:
                logger.debug(f"按ID未找到工作流，尝试按名称查找: {workflow_id}")

            workflow = get_workflow_by_name(workflow_id)

        if not workflow:
            result["message"] = f"找不到工作流: {workflow_id}"
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
                # 直接使用visualize.py中的函数生成Mermaid图表
                stages = workflow_data.get("stages", {})
                if isinstance(stages, str):
                    try:
                        stages = json.loads(stages)
                    except:
                        stages = {}

                mermaid_code = generate_workflow_mermaid(workflow_data, stages)
                result["data"]["diagram"] = mermaid_code  # Add diagram to data payload
                # Message will be updated below if format is text
            except Exception as diag_e:
                logger.error(f"生成工作流图表时出错: {diag_e}", exc_info=True)
                result["data"]["diagram_error"] = str(diag_e)

        # Format for console output if not agent mode and format is text
        if output_format == "text" and not args.get("_agent_mode", False):
            # 使用format_workflow_summary获取一致格式的工作流摘要
            info = format_workflow_summary(workflow_data)

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
        result["data"] = None
        return result


def _show_session(session_id: str, verbose: bool, output_format: str, diagram: bool, args: Dict[str, Any]) -> Dict[str, Any]:
    """显示会话详情"""
    result = {"status": "error", "code": 1, "message": "", "data": None, "meta": {"command": "flow show session", "args": args}}

    try:
        # 获取数据库会话
        db_session = get_session_factory()()

        # 创建管理器
        manager = FlowSessionManager(db_session)

        # 获取会话
        flow_session = manager.get_session(session_id)
        if not flow_session:
            result["message"] = f"找不到ID为 {session_id} 的会话"
            result["code"] = 404
            return result

        # 验证工作流定义存在
        workflow_repo = WorkflowDefinitionRepository(db_session)
        workflow_def = workflow_repo.get_by_id(flow_session.workflow_id)

        if not workflow_def:
            error_msg = (
                f"错误: 会话 {session_id} 引用了不存在的工作流定义 (ID: {flow_session.workflow_id})。\n"
                "这可能是因为:\n"
                "1. 工作流定义已被删除\n"
                "2. 创建会话时使用了错误的工作流ID或名称\n\n"
                f"建议: 使用 'vc flow session delete {session_id}' 删除此错误会话，然后使用正确的工作流ID创建新会话"
            )
            result["message"] = error_msg
            result["code"] = 404
            return result

        # 获取工作流定义
        workflow = workflow_repo.get_by_id(flow_session.workflow_id) if flow_session.workflow_id else None

        # 获取会话进度信息
        progress_info = manager.get_session_progress(session_id)

        # 获取关联的工作流定义
        workflow_name = workflow.get("name", flow_session.workflow_id) if workflow else "未知工作流"

        # 准备会话数据
        session_data = (
            flow_session.to_dict()
            if hasattr(flow_session, "to_dict")
            else {
                "id": flow_session.id,
                "name": flow_session.name,
                "status": flow_session.status,
                "workflow_id": flow_session.workflow_id,
                "created_at": flow_session.created_at.isoformat() if flow_session.created_at else None,
                "updated_at": flow_session.updated_at.isoformat() if flow_session.updated_at else None,
                "current_stage_id": flow_session.current_stage_id,
                "context": flow_session.context,
            }
        )

        # 添加进度信息
        session_data["progress"] = progress_info

        # 关闭数据库会话
        db_session.close()

        result["status"] = "success"
        result["code"] = 0
        result["data"] = {"session": session_data}

        # 格式化输出
        if output_format == "text" and not args.get("_agent_mode", False):
            # 计算进度信息
            progress_percent = progress_info.get("progress_percentage", 0)
            completed_count = progress_info.get("completed_count", 0)
            total_stages = progress_info.get("total_stages", 0)

            # 构建文本输出
            info = [
                f"会话ID: {flow_session.id}",
                f"名称: {flow_session.name}",
                f"状态: {flow_session.status}",
                f"工作流: {workflow_name} (ID: {flow_session.workflow_id})",
                f"创建时间: {flow_session.created_at.strftime('%Y-%m-%d %H:%M:%S') if flow_session.created_at else '未知'}",
                f"更新时间: {flow_session.updated_at.strftime('%Y-%m-%d %H:%M:%S') if flow_session.updated_at else '未知'}",
                f"进度: {progress_percent}% ({completed_count}/{total_stages} 阶段)",
                "=" * 40,
                "阶段状态:",
            ]

            # 添加已完成阶段
            completed_stages = progress_info.get("completed_stages", [])

            # 确保completed_stages是可迭代的
            if not isinstance(completed_stages, (list, tuple, dict)):
                # 如果是整数或其他非可迭代类型，记录一个错误并使用空列表
                logger.warning(f"完成阶段数据格式错误 - 期望列表但获得: {type(completed_stages)}")
                completed_stages = []
                # 尝试通过转换修复错误类型问题
                try:
                    # 如果是整数，假设它表示已完成阶段的数量，创建一个空列表
                    if isinstance(progress_info.get("completed_stages"), int):
                        logger.info(f"尝试修复数据类型: 将整数 {progress_info.get('completed_stages')} 转换为空列表")
                        # 更新原数据
                        progress_info["completed_stages"] = []
                        completed_stages = []
                except Exception as e:
                    logger.error(f"尝试修复数据类型时出错: {str(e)}")

            for stage in completed_stages:
                completed_at = stage.get("completed_at", "")
                if completed_at:
                    try:
                        # 简化时间格式
                        completed_at = completed_at.split("T")[0] + " " + completed_at.split("T")[1][:5]
                        info.append(f"✅ {stage['name']} - 已完成 ({completed_at})")
                    except:
                        info.append(f"✅ {stage['name']} - 已完成")
                else:
                    info.append(f"✅ {stage['name']} - 已完成")

            # 添加当前阶段
            current_stage = progress_info.get("current_stage")
            if current_stage:
                info.append(f"▶️ {current_stage['name']} - 进行中")

            # 添加待处理阶段
            pending_stages = progress_info.get("pending_stages", [])

            # 确保pending_stages是可迭代的
            if not isinstance(pending_stages, (list, tuple, dict)):
                # 如果是整数或其他非可迭代类型，记录一个错误并使用空列表
                logger.warning(f"待处理阶段数据格式错误 - 期望列表但获得: {type(pending_stages)}")
                pending_stages = []
                # 尝试通过转换修复错误类型问题
                try:
                    # 如果是整数，假设它表示待处理阶段的数量，创建一个空列表
                    if isinstance(progress_info.get("pending_stages"), int):
                        logger.info(f"尝试修复数据类型: 将整数 {progress_info.get('pending_stages')} 转换为空列表")
                        # 更新原数据
                        progress_info["pending_stages"] = []
                        pending_stages = []
                except Exception as e:
                    logger.error(f"尝试修复数据类型时出错: {str(e)}")

            for stage in pending_stages:
                info.append(f"⏳ {stage['name']} - 待进行")

            # 如果verbose模式，显示上下文信息
            if verbose and flow_session.context:
                info.append("")
                info.append("上下文信息:")
                context = flow_session.context
                if isinstance(context, str):
                    try:
                        context = json.loads(context)
                    except:
                        pass

                if isinstance(context, dict):
                    for key, value in context.items():
                        if isinstance(value, (dict, list)):
                            info.append(f"  {key}: {json.dumps(value, ensure_ascii=False, indent=2)}")
                        else:
                            info.append(f"  {key}: {value}")

            # 如果需要图表，添加会话进度的可视化图表
            if diagram and workflow:
                try:
                    # 直接使用visualize.py中的函数生成Mermaid图表
                    mermaid_code = generate_session_mermaid(flow_session, workflow, progress_info)
                    info.append("")
                    info.append("会话进度图表 (Mermaid):")
                    info.append(mermaid_code)
                    result["data"]["diagram"] = mermaid_code
                except Exception as diag_e:
                    logger.error(f"生成会话图表时出错: {diag_e}", exc_info=True)
                    info.append("")
                    info.append(f"[!] 生成会话图表失败: {str(diag_e)}")

            # 设置消息
            result["message"] = "\n".join(info)

        elif output_format == "mermaid" and workflow:
            # 如果输出格式是mermaid，生成会话进度图表
            try:
                # 直接使用visualize.py中的函数
                mermaid_code = generate_session_mermaid(flow_session, workflow, progress_info)
                result["message"] = mermaid_code
                result["data"]["diagram"] = mermaid_code
            except Exception as diag_e:
                logger.error(f"生成会话图表时出错: {diag_e}", exc_info=True)
                result["message"] = f"生成会话图表失败: {str(diag_e)}"
                result["status"] = "error"
                result["code"] = 500

        return result

    except Exception as e:
        logger.error(f"显示会话信息时出错: {str(e)}", exc_info=True)
        result["message"] = f"显示会话信息时出错: {str(e)}"
        result["code"] = 500
        result["data"] = None
        return result


# 为了向后兼容，保留原来的函数名
handle_show_session = _show_session
