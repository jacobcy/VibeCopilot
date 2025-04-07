#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上下文提供器

为AI代理提供当前工作流上下文信息
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ContextProvider:
    """上下文提供器，为AI代理提供当前工作流状态和下一步指导"""

    def __init__(self, workflows_dir: str = None):
        """
        初始化上下文提供器

        Args:
            workflows_dir: 工作流目录
        """
        self.workflows_dir = workflows_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows"
        )

    def provide_context_to_agent(
        self, workflow_id: str, progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        为AI代理提供工作流上下文

        Args:
            workflow_id: 工作流ID
            progress_data: 进度数据，包含当前阶段和已完成项

        Returns:
            上下文数据
        """
        # 加载工作流定义
        workflow = self._load_workflow(workflow_id)
        if not workflow:
            return {"error": f"找不到工作流: {workflow_id}"}

        # 确定当前阶段
        current_stage = self._determine_current_stage(workflow, progress_data)
        if not current_stage:
            return {"error": f"无法确定当前阶段: {workflow_id}"}

        # 计算进度
        progress = self._calculate_progress(workflow, current_stage, progress_data)

        # 获取下一步任务
        next_tasks = self._get_next_tasks(workflow, current_stage, progress_data)

        # 构建上下文
        context = {
            "workflow": {
                "id": workflow.get("id"),
                "name": workflow.get("name"),
                "description": workflow.get("description"),
                "source_rule": workflow.get("source_rule"),
                "total_stages": len(workflow.get("stages", [])),
            },
            "current_stage": {
                "stage_id": current_stage.get("id"),
                "stage_name": current_stage.get("name"),
                "stage_description": current_stage.get("description"),
                "stage_order": current_stage.get("order"),
                "progress": progress,
                "checklist": self._format_checklist(
                    current_stage.get("checklist", []), progress_data
                ),
                "deliverables": current_stage.get("deliverables", []),
            },
            "next_tasks": next_tasks,
        }

        # 添加后续阶段
        next_stages = self._get_next_stages(workflow, current_stage)
        if next_stages:
            context["next_stages"] = [
                {
                    "stage_id": stage.get("id"),
                    "stage_name": stage.get("name"),
                    "stage_description": stage.get("description"),
                    "stage_order": stage.get("order"),
                }
                for stage in next_stages
            ]

        return context

    def _load_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        加载工作流定义

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流定义
        """
        workflow_path = os.path.join(self.workflows_dir, f"{workflow_id}.json")
        if not os.path.exists(workflow_path):
            # 尝试只使用ID部分(不含-workflow后缀)
            base_id = workflow_id.replace("-workflow", "")
            workflow_path = os.path.join(self.workflows_dir, f"{base_id}-workflow.json")
            if not os.path.exists(workflow_path):
                logger.error(f"工作流文件不存在: {workflow_id}")
                return None

        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                workflow = json.load(f)
            return workflow
        except Exception as e:
            logger.error(f"加载工作流失败: {workflow_path}, 错误: {str(e)}")
            return None

    def _determine_current_stage(
        self, workflow: Dict[str, Any], progress_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        确定当前阶段

        Args:
            workflow: 工作流定义
            progress_data: 进度数据

        Returns:
            当前阶段
        """
        stages = workflow.get("stages", [])
        if not stages:
            return None

        # 如果指定了当前阶段ID
        stage_id = progress_data.get("current_stage")
        if stage_id:
            for stage in stages:
                if stage.get("id") == stage_id:
                    return stage

        # 默认返回第一个阶段
        return stages[0]

    def _format_checklist(
        self, checklist: List[str], progress_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        格式化检查清单

        Args:
            checklist: 检查清单
            progress_data: 进度数据

        Returns:
            格式化的检查清单
        """
        completed_items = progress_data.get("completed_items", [])
        return [{"text": item, "completed": item in completed_items} for item in checklist]

    def _calculate_progress(
        self, workflow: Dict[str, Any], current_stage: Dict[str, Any], progress_data: Dict[str, Any]
    ) -> float:
        """
        计算当前进度

        Args:
            workflow: 工作流定义
            current_stage: 当前阶段
            progress_data: 进度数据

        Returns:
            进度百分比
        """
        checklist = current_stage.get("checklist", [])
        if not checklist:
            # 如果没有检查项，按阶段计算
            stages = workflow.get("stages", [])
            stage_order = current_stage.get("order", 0)
            return (stage_order / len(stages)) * 100

        # 根据检查项计算
        completed_items = progress_data.get("completed_items", [])
        completed_count = sum(1 for item in checklist if item in completed_items)
        return (completed_count / len(checklist)) * 100

    def _get_next_tasks(
        self, workflow: Dict[str, Any], current_stage: Dict[str, Any], progress_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        获取下一步任务

        Args:
            workflow: 工作流定义
            current_stage: 当前阶段
            progress_data: 进度数据

        Returns:
            下一步任务列表
        """
        next_tasks = []
        completed_items = progress_data.get("completed_items", [])

        # 添加未完成的检查项
        for item in current_stage.get("checklist", []):
            if item not in completed_items:
                next_tasks.append(
                    {"text": item, "priority": "high", "stage_id": current_stage.get("id")}
                )

        # 如果当前阶段所有检查项都已完成，添加下一阶段的首要任务
        if not next_tasks:
            next_stages = self._get_next_stages(workflow, current_stage)
            if next_stages:
                next_stage = next_stages[0]
                if next_stage.get("checklist"):
                    next_tasks.append(
                        {
                            "text": f"准备进入下一阶段: {next_stage.get('name')}",
                            "priority": "medium",
                            "stage_id": next_stage.get("id"),
                        }
                    )
                    next_tasks.append(
                        {
                            "text": next_stage.get("checklist")[0],
                            "priority": "medium",
                            "stage_id": next_stage.get("id"),
                        }
                    )

        return next_tasks

    def _get_next_stages(
        self, workflow: Dict[str, Any], current_stage: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        获取后续阶段

        Args:
            workflow: 工作流定义
            current_stage: 当前阶段

        Returns:
            后续阶段列表
        """
        stages = workflow.get("stages", [])
        transitions = workflow.get("transitions", [])

        # 通过转换规则获取
        next_stage_ids = []
        for transition in transitions:
            if transition.get("from_stage") == current_stage.get("id"):
                next_stage_ids.append(transition.get("to_stage"))

        # 如果没有明确的转换规则，使用顺序关系
        if not next_stage_ids:
            current_order = current_stage.get("order", 0)
            for stage in stages:
                if stage.get("order", 0) == current_order + 1:
                    next_stage_ids.append(stage.get("id"))

        # 查找对应的阶段
        next_stages = []
        for stage_id in next_stage_ids:
            for stage in stages:
                if stage.get("id") == stage_id:
                    next_stages.append(stage)
                    break

        return next_stages
