#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Node.js环境配置模块入口。
该模块现已拆分为多个子模块，提高可维护性。
"""

# 导入主设置函数
from .node.setup import setup_node_environment

# 为向后兼容，保留原函数名
# 所有功能现已移到node/目录下的模块中
__all__ = ["setup_node_environment"]
