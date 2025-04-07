#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程转换器

将规则结构转换为工作流定义
"""

import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FlowConverter:
    """流程转换器，将规则数据转换为工作流定义"""

    def __init__(self):
        self.checklist_pattern = re.compile(r"^[-*]\s+(.+)$", re.MULTILINE)
        self.deliverable_pattern = re.compile(r"交付物[:：](.+?)(?=\n\n|\n#|\n$|$)", re.DOTALL)
        self.transition_pattern = re.compile(r"([^→]+)→([^→]+)", re.DOTALL)

    def convert_rule_to_workflow(self, rule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        将规则数据转换为工作流定义

        Args:
            rule_data: 规则数据

        Returns:
            工作流定义
        """
        if not rule_data:
            logger.error("无效的规则数据")
            return None

        try:
            # 提取基本信息
            rule_id = rule_data.get("rule_id", "")
            metadata = rule_data.get("metadata", {})
            rule_name = metadata.get("title", rule_id)

            # 创建工作流基本结构
            workflow = {
                "id": f"{rule_id}-workflow",
                "name": f"{rule_name} 工作流",
                "description": metadata.get("description", ""),
                "version": metadata.get("version", "1.0.0"),
                "source_rule": rule_id,
                "stages": [],
                "transitions": [],
            }

            # 解析各阶段
            sections = rule_data.get("sections", [])
            for i, section in enumerate(sections):
                stage = self._convert_section_to_stage(section, i)
                if stage:
                    workflow["stages"].append(stage)

            # 根据段落顺序添加默认转换
            for i in range(len(workflow["stages"]) - 1):
                workflow["transitions"].append(
                    {
                        "id": f"t{i+1}",
                        "from_stage": workflow["stages"][i]["id"],
                        "to_stage": workflow["stages"][i + 1]["id"],
                        "condition": "自动",
                        "description": f"从 {workflow['stages'][i]['name']} 到 {workflow['stages'][i+1]['name']}",
                    }
                )

            # 解析特殊转换条件
            self._parse_transitions(workflow, rule_data.get("raw_content", ""))

            return workflow
        except Exception as e:
            logger.error(f"转换规则到工作流失败: {str(e)}")
            return None

    def _convert_section_to_stage(
        self, section: Dict[str, Any], order: int
    ) -> Optional[Dict[str, Any]]:
        """
        将段落转换为工作流阶段

        Args:
            section: 段落数据
            order: 阶段顺序

        Returns:
            阶段定义
        """
        if not section:
            return None

        title = section.get("title", "")
        content = section.get("content", "")

        stage_id = f"stage_{order+1}"
        stage = {
            "id": stage_id,
            "name": title,
            "description": self._extract_description(content),
            "order": order,
            "checklist": self._extract_checklist(content),
            "deliverables": self._extract_deliverables(content),
        }

        return stage

    def _extract_description(self, content: str) -> str:
        """
        提取描述文本

        Args:
            content: 内容文本

        Returns:
            描述文本
        """
        # 获取第一段作为描述
        paragraphs = content.split("\n\n")
        if paragraphs:
            return paragraphs[0].strip()
        return ""

    def _extract_checklist(self, content: str) -> List[str]:
        """
        提取检查清单项

        Args:
            content: 内容文本

        Returns:
            检查清单项列表
        """
        checklist = []
        for match in self.checklist_pattern.finditer(content):
            item = match.group(1).strip()
            if item:
                checklist.append(item)
        return checklist

    def _extract_deliverables(self, content: str) -> List[str]:
        """
        提取交付物

        Args:
            content: 内容文本

        Returns:
            交付物列表
        """
        deliverables = []
        match = self.deliverable_pattern.search(content)
        if match:
            deliverable_text = match.group(1).strip()
            for item in re.split(r"[,，;；\n]", deliverable_text):
                item = item.strip()
                if item:
                    deliverables.append(item)
        return deliverables

    def _parse_transitions(self, workflow: Dict[str, Any], content: str) -> None:
        """
        解析转换条件

        Args:
            workflow: 工作流定义
            content: 原始内容
        """
        # 构建阶段名称到ID的映射
        stage_map = {stage["name"]: stage["id"] for stage in workflow["stages"]}

        # 查找所有转换表达式
        for match in self.transition_pattern.finditer(content):
            from_stage = match.group(1).strip()
            to_stage = match.group(2).strip()

            if from_stage in stage_map and to_stage in stage_map:
                # 检查是否已存在相同的转换
                transition_exists = False
                for t in workflow["transitions"]:
                    if (
                        t["from_stage"] == stage_map[from_stage]
                        and t["to_stage"] == stage_map[to_stage]
                    ):
                        transition_exists = True
                        break

                if not transition_exists:
                    workflow["transitions"].append(
                        {
                            "id": f"t{len(workflow['transitions'])+1}",
                            "from_stage": stage_map[from_stage],
                            "to_stage": stage_map[to_stage],
                            "condition": "条件",
                            "description": f"从 {from_stage} 到 {to_stage} 的条件转换",
                        }
                    )
