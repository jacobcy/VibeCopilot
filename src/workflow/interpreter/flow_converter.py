#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流程转换器

将规则结构转换为工作流定义
"""

import logging
from typing import Any, Dict, Optional

from src.llm.llm_interface import LLMInterface
from src.parsing.processors.workflow_processor import WorkflowProcessor
from src.validation.core.workflow_validator import WorkflowValidator

logger = logging.getLogger(__name__)


class FlowConverter:
    """流程转换器，将规则数据转换为工作流定义"""

    def __init__(self, llm: LLMInterface):
        """
        初始化流程转换器

        Args:
            llm: LLM接口实例
        """
        self.workflow_processor = WorkflowProcessor(llm)
        self.workflow_validator = WorkflowValidator()

    async def convert_rule_to_workflow(self, rule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
            logger.info("开始将规则转换为工作流...")

            # 使用WorkflowProcessor解析规则内容
            workflow = await self.workflow_processor.parse_workflow_rule(rule_data.get("raw_content", ""))
            if not workflow:
                logger.error("工作流解析失败")
                return None

            logger.info(f"工作流转换完成: {workflow['name']}")
            return workflow

        except Exception as e:
            logger.error(f"转换规则到工作流失败: {str(e)}")
            return None

    def convert_to_workflow(self, rule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        将规则数据转换为工作流定义

        Args:
            rule_data: 规则数据

        Returns:
            工作流定义
        """
        try:
            logger.info(f"开始转换规则 '{rule_data.get('rule_id', '')}' 为工作流...")

            # 提取工作流基本信息
            workflow = self._extract_workflow_info(rule_data)
            if not workflow:
                logger.error("工作流基本信息提取失败")
                return None

            # 提取阶段定义
            stages = self._extract_stages(rule_data)
            if not stages:
                logger.error("工作流阶段提取失败")
                return None
            workflow["stages"] = stages

            # 提取转换定义
            transitions = self._extract_transitions(rule_data)
            if not transitions:
                logger.error("工作流转换提取失败")
                return None
            workflow["transitions"] = transitions

            # 验证工作流定义
            is_valid, errors = self.workflow_validator.validate_workflow(workflow)
            if not is_valid:
                logger.error("工作流验证失败:")
                for error in errors:
                    logger.error(f"  - {error}")
                return None

            logger.info(f"工作流 '{workflow['name']}' 转换完成")
            return workflow

        except Exception as e:
            logger.error(f"工作流转换失败: {str(e)}")
            return None

    def _extract_workflow_info(self, rule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        提取工作流基本信息

        Args:
            rule_data: 规则数据

        Returns:
            工作流基本信息
        """
        try:
            metadata = rule_data.get("metadata", {})
            workflow = {
                "id": f"{rule_data['rule_id']}-workflow",
                "name": f"{metadata.get('title', '')} 工作流",
                "description": metadata.get("description", ""),
                "version": metadata.get("version", "1.0.0"),
                "source_rule": rule_data["rule_id"],
            }
            logger.debug(f"提取工作流基本信息: {workflow}")
            return workflow

        except Exception as e:
            logger.error(f"工作流基本信息提取失败: {str(e)}")
            return None

    def _extract_stages(self, rule_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        提取工作流阶段定义

        Args:
            rule_data: 规则数据

        Returns:
            工作流阶段列表
        """
        try:
            content = rule_data.get("content", {})
            if not content:
                raise ValueError("规则内容为空")

            stages = content.get("stages", [])
            if not stages:
                raise ValueError("未找到阶段定义")

            logger.debug(f"提取到 {len(stages)} 个工作流阶段")
            return stages

        except Exception as e:
            logger.error(f"工作流阶段提取失败: {str(e)}")
            return None

    def _extract_transitions(self, rule_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        提取工作流转换定义

        Args:
            rule_data: 规则数据

        Returns:
            工作流转换列表
        """
        try:
            content = rule_data.get("content", {})
            if not content:
                raise ValueError("规则内容为空")

            transitions = content.get("transitions", [])
            if not transitions:
                raise ValueError("未找到转换定义")

            logger.debug(f"提取到 {len(transitions)} 个工作流转换")
            return transitions

        except Exception as e:
            logger.error(f"工作流转换提取失败: {str(e)}")
            return None
