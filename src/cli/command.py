#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令接口定义

定义命令的基本接口
"""

from abc import ABC, abstractmethod
from typing import List


class Command(ABC):
    """命令接口，定义命令的基本方法"""

    @abstractmethod
    def execute(self, args: List[str]) -> int:
        """
        执行命令

        Args:
            args: 命令行参数列表

        Returns:
            命令执行结果状态码
        """
        pass

    @classmethod
    def get_help(cls) -> str:
        """
        获取命令的帮助信息

        Returns:
            命令的帮助文本
        """
        return cls.__doc__ or "暂无帮助信息"
