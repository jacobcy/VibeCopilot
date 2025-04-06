"""
状态同步适配器包

提供将系统状态同步到外部服务(如n8n)的功能
"""

from adapters.status_sync.adapter import StatusSyncAdapter
from adapters.status_sync.services import ExecutionSync, N8nSync, WorkflowSync

__all__ = ["StatusSyncAdapter", "WorkflowSync", "ExecutionSync", "N8nSync"]
