"""
任务命令基类模块

为task_typer包提供基础命令类
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


class BaseCommand(ABC):
    """命令基类"""

    def __init__(self, name: str, description: str):
        """初始化命令"""
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行命令

        Returns:
            Dict[str, Any]: 包含执行结果的字典，格式为:
            {
                "status": "success" | "error",
                "code": int,
                "message": str,
                "data": Optional[Any],
                "meta": Optional[Dict]
            }
        """
        pass

    def format_result(self, result: Dict[str, Any], format: str = "yaml") -> str:
        """格式化输出结果"""
        pass
