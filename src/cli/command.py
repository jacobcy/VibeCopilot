"""命令基类模块

定义了命令行接口所需的基本命令结构和接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Command(ABC):
    """命令基类，所有命令都应继承此类"""

    @classmethod
    @abstractmethod
    def get_command(cls) -> str:
        """
        获取命令名称

        Returns:
            str: 命令名称
        """
        pass

    @classmethod
    @abstractmethod
    def get_description(cls) -> str:
        """
        获取命令描述

        Returns:
            str: 命令描述
        """
        pass

    @classmethod
    @abstractmethod
    def get_help(cls) -> str:
        """
        获取命令帮助信息

        Returns:
            str: 命令帮助信息
        """
        pass

    @abstractmethod
    def parse_args(self, args: List[str]) -> Dict:
        """
        解析命令参数

        Args:
            args: 命令行参数列表

        Returns:
            Dict: 解析后的参数字典
        """
        pass

    @abstractmethod
    def execute(self, parsed_args: Dict) -> None:
        """
        执行命令

        Args:
            parsed_args: 解析后的参数字典
        """
        pass
