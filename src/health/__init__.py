"""
VibeCopilot 系统健康检查模块

提供系统各组件的健康状态检查功能，包括：
- 命令可用性检查
- 数据库完整性检查
- 文档完整性检查
- 依赖项检查
"""

from .health_check import HealthCheck

__all__ = ["HealthCheck"]
