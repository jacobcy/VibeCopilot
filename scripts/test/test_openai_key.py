#!/usr/bin/env python3
"""
测试OpenAI API密钥是否有效
"""

import json
import os
import sys

import requests


def test_openai_key(api_key):
    """测试OpenAI API密钥是否有效

    Args:
        api_key: OpenAI API密钥

    Returns:
        bool: 密钥是否有效
    """
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, are you working?"},
        ],
        "max_tokens": 10,
    }

    try:
        print(f"正在测试OpenAI API密钥...")
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"API响应成功! 回复: {content}")
            print(f"模型: {result.get('model', '未知')}")

            # 打印更多API信息
            print(f"\nAPI详情:")
            print(f"- 组织ID: {response.headers.get('openai-organization', '未知')}")
            print(f"- 请求ID: {response.headers.get('x-request-id', '未知')}")
            print(f"- 处理时间: {response.headers.get('openai-processing-ms', '未知')}ms")

            return True
        else:
            error_info = response.json() if response.text else {"error": {"message": "未知错误"}}
            print(f"API响应失败，状态码: {response.status_code}")
            print(f"错误信息: {error_info.get('error', {}).get('message', '未知错误')}")
            return False

    except Exception as e:
        print(f"测试OpenAI API时出错: {str(e)}")
        return False


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


def main():
    # 直接从.env文件读取密钥
    api_key = extract_api_key_from_env_file()

    if not api_key:
        print("错误: 无法从.env文件中提取OPENAI_API_KEY")
        sys.exit(1)

    print(f"已从.env文件中获取API密钥: {api_key[:4]}...{api_key[-4:]}")

    # 测试密钥
    is_valid = test_openai_key(api_key)

    if is_valid:
        print("\n✅ OpenAI API密钥有效，可以使用!")
    else:
        print("\n❌ OpenAI API密钥无效或API调用失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
