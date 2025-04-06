#!/usr/bin/env python3
"""
知识提取器模块
从文档中提取实体和关系
"""

import json
import os
from typing import Dict, List, Optional, Union

from langchain_openai import ChatOpenAI

from adapters.basic_memory.utils.api_utils import get_openai_api_key


class KnowledgeExtractor:
    """知识提取器

    使用大语言模型从文本中提取实体和关系
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        """初始化知识提取器

        Args:
            model: 使用的LLM模型名称
        """
        self.model = model

        # 确保API密钥已设置
        api_key = get_openai_api_key()
        if not api_key:
            raise ValueError("错误: 未设置OPENAI_API_KEY环境变量")

        # 初始化LLM
        self.llm = ChatOpenAI(model=model, temperature=0)

        # 定义提取系统提示
        self.system_prompt = """
你是一个专业的知识提取AI，负责从文本中提取结构化知识。
你需要识别文本中的关键实体和它们之间的关系，并以JSON格式输出。

每个实体应包含：
1. name: 实体名称
2. type: 实体类型（人物、组织、概念、地点、产品等）
3. description: 实体描述（基于文本内容）

每个关系应包含：
1. source: 源实体名称
2. target: 目标实体名称
3. type: 关系类型（例如：包含、属于、创建、使用、定义等）

只提取文本中明确存在的实体和关系，不要添加推测内容。
你的输出必须是有效的JSON格式，且只包含提取到的知识，不要包含任何其他内容。
"""

    def extract_from_chunk(self, text_chunk: str, context: Optional[str] = None) -> Dict:
        """从文本块中提取知识

        Args:
            text_chunk: 文本块
            context: 上下文信息

        Returns:
            Dict: 提取的知识，包含实体和关系
        """
        # 构建提示
        prompt = text_chunk
        if context:
            prompt = f"上下文：{context}\n\n文本：{text_chunk}"

        # 构建用户消息
        user_message = f"""
请从以下文本中提取实体和关系，并以JSON格式返回：

{prompt}

请确保返回的JSON格式如下：
{{
  "entities": [
    {{"name": "实体名称", "type": "实体类型", "description": "实体描述"}},
    ...
  ],
  "relations": [
    {{"source": "源实体", "target": "目标实体", "type": "关系类型"}},
    ...
  ]
}}
"""

        try:
            # 调用LLM
            response = self.llm.invoke(
                [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ]
            )

            # 解析响应
            content = response.content

            # 提取JSON部分
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
            else:
                # 如果没有找到JSON，创建空结果
                result = {"entities": [], "relations": []}
                print("警告: 无法从响应中提取JSON")

            return result
        except Exception as e:
            print(f"知识提取过程中出错: {e}")
            # 返回空结果
            return {"entities": [], "relations": []}

    def extract_from_document(self, chunks: List[str], document_title: str) -> Dict:
        """从文档中提取知识

        Args:
            chunks: 文档块列表
            document_title: 文档标题

        Returns:
            Dict: 提取的知识，包含实体和关系
        """
        print(f"正在从文档提取知识: {document_title}")

        # 创建文档实体
        document_entity = {
            "name": document_title,
            "type": "document",
            "description": f"文档标题: {document_title}",
        }

        # 初始化结果
        combined_result = {
            "entities": [document_entity],
            "relations": [],
            "observations": [],  # 存储文档观察或关键段落
        }

        # 提取每个块的知识
        for i, chunk in enumerate(chunks):
            print(f"处理块 {i+1}/{len(chunks)}")

            # 使用文档标题作为上下文
            context = f"文档: {document_title}"

            # 提取知识
            chunk_result = self.extract_from_chunk(chunk, context)

            # 将块添加为观察
            if chunk.strip():
                combined_result["observations"].append(chunk.strip())

            # 合并实体（去重）
            entity_names = {e["name"] for e in combined_result["entities"]}
            for entity in chunk_result.get("entities", []):
                if entity["name"] not in entity_names:
                    combined_result["entities"].append(entity)
                    entity_names.add(entity["name"])

            # 添加关系
            combined_result["relations"].extend(chunk_result.get("relations", []))

        # 对每个实体添加与文档的关系
        entity_names = {e["name"] for e in combined_result["entities"]}
        for entity_name in entity_names:
            if entity_name != document_title:
                combined_result["relations"].append(
                    {"source": document_title, "target": entity_name, "type": "contains"}
                )

        return combined_result

    def extract_batch(self, documents: List[Dict], chunks_map: Dict) -> List[Dict]:
        """从多个文档中批量提取知识

        Args:
            documents: 文档列表
            chunks_map: 文档标题到块列表的映射

        Returns:
            List[Dict]: 提取的知识列表
        """
        results = []

        for doc in documents:
            title = doc["title"]
            chunks = chunks_map.get(title, [])

            if not chunks:
                # 如果没有找到块，使用整个文档内容
                chunks = [doc["content"]]

            # 从文档中提取知识
            doc_result = self.extract_from_document(chunks, title)

            # 添加文档元数据
            doc_result["document_title"] = title
            doc_result["document_type"] = doc.get("metadata", {}).get("type", "unknown")
            doc_result["source_path"] = doc.get("metadata", {}).get("source", "")

            results.append(doc_result)

        return results
