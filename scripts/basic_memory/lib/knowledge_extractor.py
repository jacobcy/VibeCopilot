#!/usr/bin/env python3
"""
知识提取模块，负责从文本中提取实体和关系
"""

from typing import Dict, List, Optional

from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from scripts.basic_memory.lib.utils import get_openai_api_key


class Entity(BaseModel):
    """实体模型"""

    name: str = Field(description="实体名称")
    type: str = Field(description="实体类型")
    description: Optional[str] = Field(description="实体描述")


class Relation(BaseModel):
    """关系模型"""

    source: str = Field(description="关系源实体")
    target: str = Field(description="关系目标实体")
    type: str = Field(description="关系类型")
    description: Optional[str] = Field(description="关系描述")


class ExtractionResult(BaseModel):
    """提取结果模型"""

    document_type: Optional[str] = Field(description="文档类型")
    main_topic: Optional[str] = Field(description="主要主题")
    entities: List[Entity] = Field(description="提取的实体列表")
    relations: List[Relation] = Field(description="提取的关系列表")
    observations: List[str] = Field(description="关键观察点列表")
    tags: Optional[List[str]] = Field(description="标签列表")


class KnowledgeExtractor:
    """知识提取器"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """初始化知识提取器

        Args:
            model: 使用的OpenAI模型名称
        """
        self.model = model
        self.api_key = get_openai_api_key()

        if not self.api_key:
            raise ValueError("无法获取OpenAI API密钥，请检查环境变量或.env文件")

        # 初始化OpenAI模型
        callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
        self.llm = ChatOpenAI(model=self.model, temperature=0.2, streaming=False, verbose=False)

        # 创建结构化输出模型
        self.structured_llm = self.llm.with_structured_output(ExtractionResult)

    def extract_entities_and_relations(self, chunk_text: str, doc_title: str) -> Dict:
        """使用LLM提取实体和关系

        Args:
            chunk_text: 文本块内容
            doc_title: 文档标题

        Returns:
            Dict: 包含提取结果的字典
        """
        # 构建提示
        prompt = f"""分析以下文本片段，提取主要实体和关系。

文档标题: {doc_title}

文本内容:
{chunk_text}

请提取:
1. 文档类型和主题
2. 所有重要的实体、概念、组件
3. 实体之间的关系
4. 关键的观察点和见解
5. 相关标签

注意:
- 只提取确实存在于文本中的实体和关系
- 实体名称应简洁明确
- 关系必须有明确的源和目标
"""

        try:
            # 执行提取
            result = self.structured_llm.invoke(prompt)

            # 将结果转换为字典
            result_dict = result.model_dump()

            return result_dict
        except Exception as e:
            print(f"提取实体和关系时出错: {e}")
            return {
                "document_type": "unknown",
                "main_topic": doc_title,
                "entities": [],
                "relations": [],
                "observations": ["文本内容无法解析"],
                "tags": [],
            }
