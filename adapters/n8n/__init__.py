"""
n8n适配器模块

提供与n8n工作流引擎集成的适配器功能
"""

from adapters.n8n.adapter import N8nAdapter
from adapters.n8n.client import (
    N8nCredentialClient,
    N8nExecutionClient,
    N8nHttpClient,
    N8nVariableClient,
    N8nWorkflowClient,
)

__all__ = [
    # 兼容层
    "N8nAdapter",
    # 客户端模块
    "N8nHttpClient",
    "N8nWorkflowClient",
    "N8nExecutionClient",
    "N8nCredentialClient",
    "N8nVariableClient",
]
