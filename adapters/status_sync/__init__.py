"""
状态同步适配器模块
负责将本地SQLite状态库中的任务状态同步到外部系统
"""

from adapters.status_sync.adapter import StatusSyncAdapter

__all__ = ["StatusSyncAdapter"]
