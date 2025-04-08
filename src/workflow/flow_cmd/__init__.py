#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流命令模块

提供从命令行创建和管理工作流的功能
"""

from src.workflow.flow_cmd.workflow_creator import create_workflow_from_rule, create_workflow_from_template_with_vars
from src.workflow.flow_cmd.workflow_runner import run_workflow_stage

__all__ = [
    # 工作流创建
    "create_workflow_from_rule",
    "create_workflow_from_template_with_vars",
    # 工作流运行
    "run_workflow_stage",
]
