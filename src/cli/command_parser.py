#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令解析器

负责解析命令行参数，识别命令名称和参数
"""

import sys
from typing import List, Optional, Tuple


class CommandParser:
    """命令解析器"""

    def parse_command(self) -> Tuple[str, List[str]]:
        """
        解析命令行参数

        Returns:
            (命令名称, 命令参数)
        """
        # 获取命令行参数（跳过脚本名称）
        args = sys.argv[1:]

        # 如果没有参数，默认为help命令
        if not args:
            return "help", []

        # 获取命令名称
        command_name = args.pop(0)

        # 返回命令名称和剩余参数
        return command_name, args
