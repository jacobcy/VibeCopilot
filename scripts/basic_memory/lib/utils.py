#!/usr/bin/env python3
"""
通用工具函数，如API密钥获取等
"""

import os


def extract_api_key_from_env_file(env_path=".env"):
    """从.env文件中提取API密钥

    Args:
        env_path: .env文件路径

    Returns:
        str: API密钥
    """
    try:
        with open(env_path, "r") as f:
            for line in f:
                if line.strip().startswith("OPENAI_API_KEY="):
                    key = line.strip().split("=", 1)[1].strip()
                    # 去掉可能的引号
                    key = key.strip('"').strip("'")
                    return key
    except Exception as e:
        print(f"读取.env文件失败: {e}")
    return None


def get_openai_api_key():
    """获取OpenAI API密钥，优先从环境变量获取

    Returns:
        str: API密钥
    """
    # 首先尝试从环境变量获取
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key

    # 然后尝试从.env文件获取
    return extract_api_key_from_env_file()
