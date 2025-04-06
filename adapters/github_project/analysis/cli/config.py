#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置模块.

提供配置加载和管理功能，处理环境变量和默认配置。
"""

import os
from typing import Any, Dict

from dotenv import load_dotenv


def load_config() -> Dict[str, Any]:
    """加载配置.

    从环境变量加载配置项，提供项目分析所需的基本配置。

    Returns:
        Dict[str, Any]: 配置项字典
    """
    # 加载环境变量
    load_dotenv()

    config = {
        "owner": os.getenv("GITHUB_OWNER"),
        "repo": os.getenv("GITHUB_REPO"),
        "project_number": os.getenv("GITHUB_PROJECT_NUMBER"),
        "token": os.getenv("GITHUB_TOKEN"),
        "api_base_url": os.getenv("GITHUB_API_URL", "https://api.github.com"),
    }

    return config
