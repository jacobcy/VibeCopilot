#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模块

提供工作流定义、创建、执行和管理的核心功能
"""

# 导出工作流工具
from src.workflow.utils import create_workflow_from_rule, create_workflow_from_template_with_vars, get_workflow_fuzzy  # 工作流创建; 工作流搜索

# 导出子模块
__all__ = [
    # 工作流创建
    "create_workflow_from_rule",
    "create_workflow_from_template_with_vars",
    # 工作流搜索
    "get_workflow_fuzzy",
]
