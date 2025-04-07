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

    def export_workflow_with_status(
        self,
        workflow: Dict[str, Any],
        completed_stages: List[str],
        active_stages: List[str],
        pending_stages: List[str],
    ) -> str:
        """
        导出带有执行状态的工作流Mermaid流程图

        Args:
            workflow: 工作流定义
            completed_stages: 已完成阶段ID列表
            active_stages: 进行中阶段ID列表
            pending_stages: 未开始阶段ID列表

        Returns:
            带有状态颜色的Mermaid图代码
        """
        if not workflow:
            return "```mermaid\nflowchart TD\n  A[无效工作流]\n```"

        # 构建节点
        nodes = []
        stage_nodes = {}  # 存储阶段ID到节点索引的映射

        # 为终止节点添加"完成"节点
        end_node = 'end["完成"]'
        nodes.append(f"  {end_node}")

        # 处理阶段节点
        for stage in workflow.get("stages", []):
            stage_id = stage.get("id", "").replace("-", "_")
            stage_name = stage.get("name", "")

            # 确定阶段状态标签
            status_label = ""
            if stage.get("id") in completed_stages:
                status_label = "|完成|"
            elif stage.get("id") in active_stages:
                status_label = "|进行中|"
            elif stage.get("id") in pending_stages:
                status_label = "|未开始|"

            node = f'  {stage_id}["{stage_name}"]'
            nodes.append(node)
            stage_nodes[stage.get("id")] = len(nodes) - 1

        # 构建连接
        links = []
        has_transitions = False

        # 使用transitions如果有定义
        if workflow.get("transitions"):
            has_transitions = True
            for transition in workflow.get("transitions", []):
                from_id = transition.get("from_stage", "").replace("-", "_")
                to_id = transition.get("to_stage", "").replace("-", "_")
                condition = transition.get("condition", "")

                status_label = ""
                if transition.get("from_stage") in completed_stages:
                    status_label = "|完成|"
                elif transition.get("from_stage") in active_stages:
                    status_label = "|进行中|"
                elif transition.get("from_stage") in pending_stages:
                    status_label = "|未开始|"

                if condition and condition != "自动":
                    links.append(f"  {from_id} -->{status_label}|{condition}| {to_id}")
                else:
                    links.append(f"  {from_id} -->{status_label} {to_id}")

        # 否则基于dependencies构建连接
        if not has_transitions:
            for stage in workflow.get("stages", []):
                stage_id = stage.get("id", "").replace("-", "_")
                deps = stage.get("dependencies", [])

                # 如果没有依赖，查看下一个阶段
                if not deps:
                    continue

                # 为每个依赖添加连接
                for dep in deps:
                    dep_id = dep.replace("-", "_")

                    status_label = ""
                    if dep in completed_stages:
                        status_label = "|完成|"
                    elif dep in active_stages:
                        status_label = "|进行中|"
                    elif dep in pending_stages:
                        status_label = "|未开始|"

                    links.append(f"  {dep_id} -->{status_label} {stage_id}")

            # 查找没有后继的阶段，连接到end节点
            outgoing = set()
            for link in links:
                parts = link.split("-->")
                if len(parts) > 1:
                    target = parts[1].split(" ")[-1]
                    outgoing.add(target)

            for stage in workflow.get("stages", []):
                stage_id = stage.get("id", "").replace("-", "_")
                if stage_id not in outgoing:
                    status_label = ""
                    if stage.get("id") in completed_stages:
                        status_label = "|完成|"
                    elif stage.get("id") in active_stages:
                        status_label = "|进行中|"
                    elif stage.get("id") in pending_stages:
                        status_label = "|未开始|"

                    links.append(f"  {stage_id} -->{status_label} end")

        # 添加基于状态的样式
        styles = []

        # 为完成阶段添加绿色样式
        for stage_id in completed_stages:
            node_id = stage_id.replace("-", "_")
            styles.append(f"  style {node_id} fill:#c3e6cb,stroke:#28a745")

        # 为进行中阶段添加黄色样式
        for stage_id in active_stages:
            node_id = stage_id.replace("-", "_")
            styles.append(f"  style {node_id} fill:#fff3cd,stroke:#ffc107")

        # 为未开始阶段添加灰色样式
        for stage_id in pending_stages:
            node_id = stage_id.replace("-", "_")
            styles.append(f"  style {node_id} fill:#f8f9fa,stroke:#6c757d")

        # 为完成节点添加样式
        styles.append(f"  style end fill:#f8f9fa,stroke:#6c757d")

        # 组装Mermaid图
        mermaid_code = ["```mermaid", "graph TD"]
        mermaid_code.extend(nodes)
        mermaid_code.extend(links)
        mermaid_code.extend(styles)
        mermaid_code.append("```")

        return "\n".join(mermaid_code)
