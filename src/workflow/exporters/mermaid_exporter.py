#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mermaid导出工具

将工作流导出为Mermaid流程图
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MermaidExporter:
    """Mermaid导出工具，将工作流导出为Mermaid流程图"""

    def export_workflow(self, workflow: Dict[str, Any]) -> str:
        """
        导出工作流为Mermaid流程图

        Args:
            workflow: 工作流定义

        Returns:
            Mermaid图代码
        """
        if not workflow:
            return "```mermaid\nflowchart TD\n  A[无效工作流]\n```"

        # 构建节点
        nodes = []
        for stage in workflow.get("stages", []):
            stage_id = stage.get("id", "").replace("-", "_")
            stage_name = stage.get("name", "")
            nodes.append(f"  {stage_id}[{stage_name}]")

        # 构建连接
        links = []
        for transition in workflow.get("transitions", []):
            from_id = transition.get("from_stage", "").replace("-", "_")
            to_id = transition.get("to_stage", "").replace("-", "_")
            condition = transition.get("condition", "")

            if condition and condition != "自动":
                links.append(f"  {from_id} -->|{condition}| {to_id}")
            else:
                links.append(f"  {from_id} --> {to_id}")

        # 添加样式
        styles = []
        for stage in workflow.get("stages", []):
            stage_id = stage.get("id", "").replace("-", "_")
            styles.append(f"  style {stage_id} fill:#f9f,stroke:#333,stroke-width:2px")

        # 组装Mermaid图
        mermaid_code = ["```mermaid", "flowchart TD"]
        mermaid_code.extend(nodes)
        mermaid_code.extend(links)
        mermaid_code.extend(styles)
        mermaid_code.append("```")

        return "\n".join(mermaid_code)
