#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令行接口兼容层.

为保持向后兼容，此模块重定向到新的CLI子模块。新代码应直接使用cli包。
"""

from .cli.main import main

if __name__ == "__main__":
    main()
