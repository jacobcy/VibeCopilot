"""
工作流分析包

提供工作流统计和分析功能
"""

from src.workflow.analytics.workflow_analytics import _analyze_workflow_progress, calculate_progress_statistics, get_workflow_executions

__all__ = [
    "calculate_progress_statistics",
    "get_workflow_executions",
    "_analyze_workflow_progress",  # 导出供测试使用
]
