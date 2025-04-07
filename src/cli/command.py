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
