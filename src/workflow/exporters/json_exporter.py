#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON导出工具

将工作流导出为JSON格式，以及从JSON加载工作流
"""

import glob
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class JsonExporter:
    """JSON导出工具，负责工作流的JSON序列化与反序列化"""

    def __init__(self, workflows_dir: str = None):
        """
        初始化JSON导出工具

        Args:
            workflows_dir: 工作流目录
        """
        self.workflows_dir = workflows_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows"
        )

        # 确保工作流目录存在
        os.makedirs(self.workflows_dir, exist_ok=True)

    def export_workflow(self, workflow: Dict[str, Any], output_path: str = None) -> Optional[str]:
        """
        导出工作流为JSON文件

        Args:
            workflow: 工作流定义
            output_path: 输出文件路径

        Returns:
            输出文件路径
        """
        if not workflow:
            logger.error("无效的工作流")
            return None

        try:
            # 确定输出路径
            if not output_path:
                workflow_id = workflow.get("id", "workflow")
                output_path = os.path.join(self.workflows_dir, f"{workflow_id}.json")

            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            # 导出JSON
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(workflow, f, ensure_ascii=False, indent=2)

            logger.info(f"工作流已导出到: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"导出工作流失败: {str(e)}")
            return None

    def load_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        从JSON文件加载工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流定义
        """
        try:
            workflow_path = os.path.join(self.workflows_dir, f"{workflow_id}.json")
            if not os.path.exists(workflow_path):
                logger.error(f"工作流文件不存在: {workflow_id}")
                return None

            with open(workflow_path, "r", encoding="utf-8") as f:
                workflow = json.load(f)

            return workflow
        except Exception as e:
            logger.error(f"加载工作流失败: {workflow_id}, 错误: {str(e)}")
            return None

    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        列出所有工作流

        Returns:
            工作流列表
        """
        workflows = []

        try:
            # 查找所有JSON文件
            pattern = os.path.join(self.workflows_dir, "*.json")
            workflow_files = glob.glob(pattern)

            for file_path in workflow_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        workflow = json.load(f)

                    # 提取基本信息
                    workflows.append(
                        {
                            "id": workflow.get("id", ""),
                            "name": workflow.get("name", ""),
                            "description": workflow.get("description", ""),
                            "source_rule": workflow.get("source_rule", ""),
                            "file_path": file_path,
                        }
                    )
                except Exception as e:
                    logger.warning(f"加载工作流失败: {file_path}, 错误: {str(e)}")

            return workflows
        except Exception as e:
            logger.error(f"列出工作流失败: {str(e)}")
            return []
