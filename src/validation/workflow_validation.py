"""
工作流验证

提供工作流结构和内容的验证函数
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from src.core.exceptions import ValidationError


def validate_workflow_structure(workflow_data: Dict[str, Any]) -> None:
    """
    验证工作流结构的完整性

    Args:
        workflow_data: 工作流数据字典

    Raises:
        ValidationError: 如果验证失败
    """
    if not isinstance(workflow_data, dict):
        raise ValidationError("Invalid workflow data format")

    # 检查必要字段
    required_fields = ["stages", "transitions"]
    missing_fields = [f for f in required_fields if f not in workflow_data]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    # 验证stages和transitions是否为列表
    if not isinstance(workflow_data["stages"], list):
        raise ValidationError("Stages must be a list")

    if not isinstance(workflow_data["transitions"], list):
        raise ValidationError("Transitions must be a list")


def validate_stages(stages: list) -> Set[str]:
    """
    验证工作流阶段的有效性

    Args:
        stages: 工作流阶段列表

    Returns:
        有效的阶段ID集合

    Raises:
        ValidationError: 如果验证失败
    """
    stage_ids = set()
    for stage in stages:
        # 验证必要字段
        required_fields = ["id", "name", "description", "checklist", "deliverables"]
        missing_fields = [f for f in required_fields if f not in stage]
        if missing_fields:
            raise ValidationError(f"Stage missing required fields: {', '.join(missing_fields)}")

        # 验证ID唯一性
        if stage["id"] in stage_ids:
            raise ValidationError(f"Duplicate stage ID: {stage['id']}")
        stage_ids.add(stage["id"])

        # 验证列表字段
        if not isinstance(stage["checklist"], list):
            raise ValidationError(f"Stage {stage['id']}: checklist must be a list")

        if not isinstance(stage["deliverables"], list):
            raise ValidationError(f"Stage {stage['id']}: deliverables must be a list")

    return stage_ids


def validate_transitions(transitions: list, valid_stage_ids: Set[str]) -> None:
    """
    验证工作流转换的有效性

    Args:
        transitions: 工作流转换列表
        valid_stage_ids: 有效的阶段ID集合

    Raises:
        ValidationError: 如果验证失败
    """
    transition_ids = set()
    for transition in transitions:
        # 验证必要字段
        required_fields = ["id", "from_stage", "to_stage", "condition", "description"]
        missing_fields = [f for f in required_fields if f not in transition]
        if missing_fields:
            raise ValidationError(f"Transition missing required fields: {', '.join(missing_fields)}")

        # 验证ID唯一性
        if transition["id"] in transition_ids:
            raise ValidationError(f"Duplicate transition ID: {transition['id']}")
        transition_ids.add(transition["id"])

        # 验证阶段存在性
        if transition["from_stage"] not in valid_stage_ids:
            raise ValidationError(f"Invalid from_stage: {transition['from_stage']}")

        if transition["to_stage"] not in valid_stage_ids:
            raise ValidationError(f"Invalid to_stage: {transition['to_stage']}")


def validate_workflow_completeness(stages: list, transitions: list) -> None:
    """
    验证工作流的完整性

    Args:
        stages: 工作流阶段列表
        transitions: 工作流转换列表

    Raises:
        ValidationError: 如果验证失败
    """
    # 构建阶段连接图
    graph = defaultdict(list)
    for transition in transitions:
        graph[transition["from_stage"]].append(transition["to_stage"])

    # 检查是否有孤立的阶段
    reachable = set()

    def dfs(stage_id):
        if stage_id in reachable:
            return
        reachable.add(stage_id)
        for next_stage in graph[stage_id]:
            dfs(next_stage)

    # 从所有没有入边的阶段开始DFS
    start_stages = {s["id"] for s in stages} - {t["to_stage"] for t in transitions}
    for start in start_stages:
        dfs(start)

    # 检查是否所有阶段都可达
    unreachable = {s["id"] for s in stages} - reachable
    if unreachable:
        raise ValidationError(f"Unreachable stages found: {', '.join(unreachable)}")


def check_circular_dependencies(transitions: list) -> None:
    """
    检查工作流中的循环依赖

    Args:
        transitions: 工作流转换列表

    Raises:
        ValidationError: 如果发现循环依赖
    """
    # 构建图
    graph = defaultdict(list)
    for transition in transitions:
        graph[transition["from_stage"]].append(transition["to_stage"])

    # 检查循环
    visited = set()
    path = set()

    def has_cycle(node):
        if node in path:
            return True
        if node in visited:
            return False

        visited.add(node)
        path.add(node)

        for next_node in graph[node]:
            if has_cycle(next_node):
                return True

        path.remove(node)
        return False

    # 检查所有节点
    for node in graph:
        if node not in visited:
            if has_cycle(node):
                raise ValidationError(f"Circular dependency detected at stage: {node}")


def validate_workflow(workflow_data: Dict[str, Any]) -> None:
    """
    验证工作流的完整性

    Args:
        workflow_data: 工作流数据字典

    Raises:
        ValidationError: 如果验证失败
    """
    # 1. 验证基本结构
    validate_workflow_structure(workflow_data)

    # 2. 验证阶段
    stages = workflow_data["stages"]
    valid_stage_ids = validate_stages(stages)

    # 3. 验证转换
    transitions = workflow_data["transitions"]
    validate_transitions(transitions, valid_stage_ids)

    # 4. 验证完整性
    validate_workflow_completeness(stages, transitions)

    # 5. 检查循环依赖
    check_circular_dependencies(transitions)
