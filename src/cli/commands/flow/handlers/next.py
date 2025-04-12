"""
Flow 'next' subcommand handler.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db import get_session_factory
from src.db.repositories.flow_session_repository import FlowSessionRepository
from src.db.repositories.stage_instance_repository import StageInstanceRepository
from src.db.repositories.stage_repository import StageRepository
from src.db.repositories.workflow_definition_repository import WorkflowDefinitionRepository
from src.models.db.flow_session import FlowSession, StageInstance
from src.models.db.stage import Stage
from src.models.db.workflow_definition import WorkflowDefinition

logger = logging.getLogger(__name__)


def handle_next_subcommand(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理获取下一阶段建议子命令

    Args:
        args: 命令参数字典，包含:
            - session_id: 会话ID
            - current: (可选) 当前阶段ID，如果不提供则使用会话当前阶段
            - format: 输出格式 (json/text)
            - verbose: 是否显示详细信息

    Returns:
        命令结果字典，包含:
            - status: 状态 ("success"/"error")
            - code: 状态码
            - message: 结果消息
            - data: 结果数据
    """
    logger.debug(f"获取下一阶段建议: {args}")

    session_id = args.get("session_id")
    if not session_id:
        return {"status": "error", "code": 400, "message": "需要提供会话ID (session_id)", "data": None}

    current_stage_id = args.get("current")
    format_type = args.get("format", "text")
    verbose = args.get("verbose", False)

    try:
        session_factory = get_session_factory()
        with session_factory() as db_session:
            # 1. 获取会话信息
            session_repo = FlowSessionRepository(db_session)
            session = session_repo.get_by_id(session_id)

            if not session:
                return {"status": "error", "code": 404, "message": f"找不到ID为 '{session_id}' 的会话", "data": None}

            # 2. 获取工作流定义
            workflow_repo = WorkflowDefinitionRepository(db_session)
            workflow = workflow_repo.get_by_id(session.workflow_id)

            if not workflow:
                return {"status": "error", "code": 404, "message": f"找不到会话对应的工作流定义 (ID: {session.workflow_id})", "data": None}

            # 3. 获取当前阶段
            if not current_stage_id:
                current_stage_id = session.current_stage_id

            if not current_stage_id:
                return {"status": "error", "code": 400, "message": "无法确定当前阶段，请指定 --current 参数", "data": None}

            # 4. 获取当前阶段信息
            stage_repo = StageRepository(db_session)
            current_stage = stage_repo.get_by_id(current_stage_id)

            if not current_stage:
                return {"status": "error", "code": 404, "message": f"找不到ID为 '{current_stage_id}' 的阶段", "data": None}

            # 5. 获取工作流中的所有阶段
            all_stages = stage_repo.get_by_workflow_id(workflow.id)
            all_stages_dict = {stage.id: stage for stage in all_stages}

            # 6. 计算下一阶段
            next_stages = get_next_stages(workflow, current_stage, all_stages_dict, session)

            # 7. 格式化输出
            result_data = {
                "session": {"id": session.id, "name": session.name, "status": session.status},
                "current_stage": {"id": current_stage.id, "name": current_stage.name, "description": current_stage.description},
                "next_stages": [
                    {
                        "id": stage.id,
                        "name": stage.name,
                        "description": stage.description,
                        "weight": stage.weight,
                        "estimated_time": stage.estimated_time,
                    }
                    for stage in next_stages
                ],
                "workflow": {"id": workflow.id, "name": workflow.name},
            }

            if format_type == "json":
                message = json.dumps(result_data, ensure_ascii=False, indent=2)
            else:
                message = format_next_stages_text(result_data, verbose)

            return {"status": "success", "code": 200, "message": message, "data": result_data}

    except Exception as e:
        logger.exception(f"获取下一阶段建议失败")
        return {"status": "error", "code": 500, "message": f"获取下一阶段建议失败: {str(e)}", "data": None}


def get_next_stages(workflow: WorkflowDefinition, current_stage: Stage, all_stages_dict: Dict[str, Stage], session: FlowSession) -> List[Stage]:
    """
    根据工作流规则计算可能的下一阶段

    Args:
        workflow: 工作流定义
        current_stage: 当前阶段
        all_stages_dict: 所有阶段字典 {stage_id: Stage}
        session: 当前会话

    Returns:
        可能的下一阶段列表
    """
    # 如果是最后一个阶段，没有下一阶段
    if current_stage.is_end:
        return []

    next_stages = []
    completed_stages = session.completed_stages or []

    # 遍历所有阶段，找出满足条件的下一阶段
    for stage_id, stage in all_stages_dict.items():
        # 跳过当前阶段和已完成阶段
        if stage_id == current_stage.id or stage_id in completed_stages:
            continue

        # 检查依赖关系
        if stage.depends_on:
            depends_satisfied = True
            for dep_id in stage.depends_on:
                if dep_id not in completed_stages and dep_id != current_stage.id:
                    depends_satisfied = False
                    break

            if not depends_satisfied:
                continue

        # 检查阶段是否可访问（有些阶段可能有额外条件）
        if stage.prerequisites and not check_prerequisites(stage.prerequisites, session.context):
            continue

        next_stages.append(stage)

    # 根据权重排序
    next_stages.sort(key=lambda s: s.weight if s.weight is not None else 999)

    return next_stages


def check_prerequisites(prerequisites: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """
    检查阶段先决条件是否满足

    Args:
        prerequisites: 先决条件字典
        context: 会话上下文

    Returns:
        是否满足先决条件
    """
    # 简单实现：检查上下文中是否包含所有先决条件的键
    if not prerequisites:
        return True

    if not context:
        return False

    for key, value in prerequisites.items():
        if key not in context:
            return False

        if context[key] != value:
            return False

    return True


def format_next_stages_text(data: Dict[str, Any], verbose: bool = False) -> str:
    """
    将下一阶段信息格式化为可读文本

    Args:
        data: 下一阶段数据
        verbose: 是否显示详细信息

    Returns:
        格式化的文本
    """
    session_info = data["session"]
    current_stage = data["current_stage"]
    next_stages = data["next_stages"]
    workflow = data["workflow"]

    lines = []

    # 添加头部信息
    lines.append(f"工作流: {workflow['name']} (ID: {workflow['id']})")
    lines.append(f"会话: {session_info['name']} (ID: {session_info['id']})")
    lines.append(f"当前阶段: {current_stage['name']} (ID: {current_stage['id']})")

    if verbose:
        lines.append(f"当前阶段描述: {current_stage['description']}")

    # 添加下一阶段信息
    if not next_stages:
        lines.append("\n没有找到可用的下一阶段。这可能是最后一个阶段，或者没有满足条件的下一阶段。")
    else:
        lines.append(f"\n找到 {len(next_stages)} 个可能的下一阶段:")

        for i, stage in enumerate(next_stages, 1):
            lines.append(f"  {i}. {stage['name']} (ID: {stage['id']})")
            if verbose:
                lines.append(f"     描述: {stage['description']}")
                if stage.get("estimated_time"):
                    lines.append(f"     预计时间: {stage['estimated_time']}")

    # 添加操作建议
    lines.append("\n建议操作:")
    if next_stages:
        suggested_stage = next_stages[0]
        lines.append(f"  推荐进入下一阶段: {suggested_stage['name']}")
        lines.append(f"  执行命令: vc flow create --workflow {workflow['id']} --stage {suggested_stage['id']}")
    else:
        lines.append("  当前工作流没有推荐的下一步操作。可以考虑结束当前会话:")
        lines.append(f"  执行命令: vc flow session complete {session_info['id']}")

    return "\n".join(lines)
