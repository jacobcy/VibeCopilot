#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流验证器

验证工作流定义的格式和内容是否符合规范。
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.validation.core.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class WorkflowValidator(BaseValidator):
    """工作流验证器"""

    def __init__(self):
        """初始化工作流验证器"""
        super().__init__()

        # 工作流结构验证规则
        self.workflow_schema = {
            "type": "object",
            "required": ["id", "name", "description"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "type": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "steps": {"type": "array", "items": {"type": "object"}},
            },
            "additionalProperties": True,  # 允许其他字段存在
        }

    def validate(self, data: Any) -> ValidationResult:
        """
        实现抽象基类的验证方法

        Args:
            data: 要验证的数据

        Returns:
            ValidationResult: 验证结果
        """
        is_valid, errors = self.validate_workflow(data)
        return ValidationResult(is_valid=is_valid, data=data if is_valid else None, messages=errors)

    def validate_workflow(self, workflow: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证工作流定义

        Args:
            workflow: 工作流定义

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        try:
            # 1. 基本结构验证
            is_valid, schema_errors = self.validate_schema(workflow, self.workflow_schema)
            if not is_valid:
                errors.extend(schema_errors)
                return False, errors

            # 2. 业务规则验证（可选）
            # self._validate_business_rules(workflow, errors)

            # 3. 返回验证结果
            return len(errors) == 0, errors

        except Exception as e:
            logger.error(f"工作流验证失败: {str(e)}")
            errors.append(f"验证过程发生错误: {str(e)}")
            return False, errors

    def _validate_business_rules(self, workflow: Dict[str, Any], errors: List[str]) -> None:
        """
        验证业务规则

        Args:
            workflow: 工作流定义
            errors: 错误信息列表
        """
        # 1. 验证阶段ID唯一性
        stage_ids = set()
        for stage in workflow["stages"]:
            if stage["id"] in stage_ids:
                errors.append(f"重复的阶段ID: {stage['id']}")
            stage_ids.add(stage["id"])

        # 2. 验证转换ID唯一性
        transition_ids = set()
        for transition in workflow["transitions"]:
            if transition["id"] in transition_ids:
                errors.append(f"重复的转换ID: {transition['id']}")
            transition_ids.add(transition["id"])

        # 3. 验证转换引用的阶段是否存在
        for transition in workflow["transitions"]:
            if transition["from_stage"] not in stage_ids:
                errors.append(f"转换 {transition['id']} 引用了不存在的源阶段: {transition['from_stage']}")
            if transition["to_stage"] not in stage_ids:
                errors.append(f"转换 {transition['id']} 引用了不存在的目标阶段: {transition['to_stage']}")

        # 4. 验证工作流的完整性
        self._validate_workflow_completeness(workflow, stage_ids, errors)

    def _validate_workflow_completeness(self, workflow: Dict[str, Any], stage_ids: set, errors: List[str]) -> None:
        """
        验证工作流的完整性

        Args:
            workflow: 工作流定义
            stage_ids: 所有阶段ID集合
            errors: 错误信息列表
        """
        # 1. 确保每个阶段都有出口（除了最后一个阶段）
        for stage in workflow["stages"]:
            has_outgoing = False
            for transition in workflow["transitions"]:
                if transition["from_stage"] == stage["id"]:
                    has_outgoing = True
                    break
            if not has_outgoing and stage != workflow["stages"][-1]:
                errors.append(f"阶段 {stage['id']} 没有出口转换")

        # 2. 确保每个阶段都有入口（除了第一个阶段）
        for stage in workflow["stages"]:
            has_incoming = False
            for transition in workflow["transitions"]:
                if transition["to_stage"] == stage["id"]:
                    has_incoming = True
                    break
            if not has_incoming and stage != workflow["stages"][0]:
                errors.append(f"阶段 {stage['id']} 没有入口转换")

        # 3. 检查是否存在循环依赖
        self._check_circular_dependencies(workflow, errors)
