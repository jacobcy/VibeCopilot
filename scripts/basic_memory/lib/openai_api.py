"""
OpenAI API处理模块
提供与OpenAI API交互的功能，用于知识提取和解析
"""

import json
import os
from pathlib import Path

import requests


def extract_api_key_from_env_file(env_file_path=".env"):
    """
    从.env文件中提取OpenAI API密钥

    Args:
        env_file_path (str): .env文件路径

    Returns:
        str: OpenAI API密钥
    """
    try:
        with open(env_file_path, "r") as f:
            for line in f:
                if line.startswith("OPENAI_API_KEY="):
                    return line.strip().split("=")[1].strip('"').strip("'")
    except FileNotFoundError:
        print(f"Error: .env file not found at {env_file_path}")
    return os.environ.get("OPENAI_API_KEY")


class OpenAIClient:
    """OpenAI API客户端，处理所有OpenAI API的请求"""

    def __init__(self, model="gpt-4o-mini"):
        """
        初始化OpenAI客户端

        Args:
            model (str): 使用的OpenAI模型名称
        """
        self.api_key = extract_api_key_from_env_file()
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment or .env file")

        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def parse_content(self, content, file_path):
        """
        使用OpenAI API解析内容

        Args:
            content (str): 要解析的文档内容
            file_path (str): 文档路径

        Returns:
            dict: 解析结果，包含实体和关系
        """
        system_prompt = """
        You are an expert knowledge extractor. Your task is to extract entities and relationships from the document provided.
        Output strictly in this JSON format:
        {
            "entities": [
                {
                    "name": "entity_name",
                    "type": "entity_type",
                    "description": "brief_description"
                }
            ],
            "relationships": [
                {
                    "source": "source_entity_name",
                    "target": "target_entity_name",
                    "type": "relationship_type",
                    "description": "brief_description"
                }
            ]
        }

        Entity types should be one of: Concept, Person, Organization, Tool, Process, Technology, Other
        Relationship types should be one of: Defines, Uses, Implements, PartOf, Related, Describes, Extends

        - Focus on main concepts, technologies, methods, and dependencies.
        - Extract at least 3 and at most 20 entities
        - Extract at least 2 and at most 15 relationships
        - Keep descriptions concise (under 100 chars)
        - Only include significant entities and meaningful relationships
        - If there are no meaningful entities or relationships, provide an empty array
        """

        user_prompt = f"Document from file {file_path}:\n\n{content}"

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=data)
            response.raise_for_status()

            response_data = response.json()
            assistant_message = response_data["choices"][0]["message"]["content"]

            # 尝试解析JSON响应
            try:
                result = json.loads(assistant_message)
                # 验证结果格式
                if "entities" not in result or "relationships" not in result:
                    print(f"Error parsing {file_path}: Invalid response format")
                    return self._get_default_result(file_path)
                return result
            except json.JSONDecodeError:
                print(f"Error parsing {file_path}: Invalid JSON in response")
                return self._get_default_result(file_path)

        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")
            return self._get_default_result(file_path)

    def _get_default_result(self, file_path):
        """
        当API请求失败时返回默认结果

        Args:
            file_path (str): 文档路径

        Returns:
            dict: 默认的解析结果
        """
        filename = os.path.basename(file_path)
        return {
            "entities": [
                {"name": filename, "type": "Concept", "description": f"Content from {filename}"}
            ],
            "relationships": [],
        }
