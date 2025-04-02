"""
命令处理器基类

提供命令处理的基础功能和接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseCommand(ABC):
    """命令处理器基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行命令"""
        pass

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """验证参数"""
        return True

    def format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化响应"""
        return {"success": True, "command": self.name, "data": data}
