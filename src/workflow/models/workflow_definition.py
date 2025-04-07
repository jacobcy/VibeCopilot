#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流定义模型

定义工作流结构相关的数据结构
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowStage:
    """工作流阶段"""

    id: str
    name: str
    description: str
    order: int
    checklist: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)


@dataclass
class WorkflowTransition:
    """工作流转换"""

    from_stage: str
    to_stage: str
    condition: str


@dataclass
class WorkflowDefinition:
    """工作流定义"""

    id: str
    name: str
    description: str
    source_rule: str
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    stages: List[WorkflowStage] = field(default_factory=list)
    transitions: List[WorkflowTransition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_rule": self.source_rule,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "stages": [
                {
                    "id": stage.id,
                    "name": stage.name,
                    "description": stage.description,
                    "order": stage.order,
                    "checklist": stage.checklist,
                    "deliverables": stage.deliverables,
                }
                for stage in self.stages
            ],
            "transitions": [
                {
                    "from": transition.from_stage,
                    "to": transition.to_stage,
                    "condition": transition.condition,
                }
                for transition in self.transitions
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowDefinition":
        """从字典创建"""
        stages = [
            WorkflowStage(
                id=stage.get("id", ""),
                name=stage.get("name", ""),
                description=stage.get("description", ""),
                order=stage.get("order", 0),
                checklist=stage.get("checklist", []),
                deliverables=stage.get("deliverables", []),
            )
            for stage in data.get("stages", [])
        ]

        transitions = [
            WorkflowTransition(
                from_stage=transition.get("from", ""),
                to_stage=transition.get("to", ""),
                condition=transition.get("condition", ""),
            )
            for transition in data.get("transitions", [])
        ]

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            source_rule=data.get("source_rule", ""),
            version=data.get("version", "1.0.0"),
            created_at=data.get("created_at", time.strftime("%Y-%m-%d %H:%M:%S")),
            updated_at=data.get("updated_at", time.strftime("%Y-%m-%d %H:%M:%S")),
            stages=stages,
            transitions=transitions,
        )
