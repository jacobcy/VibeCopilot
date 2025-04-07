#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流上下文模型

定义工作流上下文相关的数据结构
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ChecklistItem:
    """检查清单项"""

    id: str
    text: str
    completed: bool = False


@dataclass
class NextTask:
    """下一步任务"""

    id: str
    text: str
    type: str  # checklist_item, stage_transition, workflow_completion
    priority: str  # high, normal, low
    next_stage_id: Optional[str] = None
    next_stage_name: Optional[str] = None


@dataclass
class StageContext:
    """阶段上下文"""

    workflow_id: str
    workflow_name: str
    stage_id: str
    stage_name: str
    stage_description: str
    checklist: List[ChecklistItem]
    deliverables: List[str]
    progress: float  # 0-100


@dataclass
class WorkflowContext:
    """工作流上下文"""

    workflow: Dict[str, Any]
    current_stage: StageContext
    next_tasks: List[NextTask]
    all_stages: List[Dict[str, Any]]
    transitions: List[Dict[str, Any]]
