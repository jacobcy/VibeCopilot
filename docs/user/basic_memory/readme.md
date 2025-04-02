# VibeCopilot 知识管理系统

VibeCopilot 知识管理系统是一个高级语义知识处理平台，结合了 LangChain 和 Basic Memory 的核心优势，实现了从原始文档到语义化知识图谱的完整工作流程。

## 核心功能

- **智能语义理解**：利用 OpenAI 和 LangChain 实现深度文档内容理解
- **向量化存储**：将文档内容向量化，支持相似度查询和语义搜索
- **知识图谱构建**：自动提取实体和关系，构建可视化知识图谱
- **内容双向流转**：支持 Markdown 文档到 Obsidian 知识库的双向导出与同步
- **自然语言查询**：支持使用自然语言直接查询知识库内容

## 系统架构

本系统由以下核心组件构成：

1. **文档解析器**：
   - `openai_parser.py` - 基于 OpenAI API 的文档解析
   - `langchain_parser.py` - 基于 LangChain 的增强解析

2. **存储系统**：
   - Basic Memory 数据库 - 存储实体和关系
   - FAISS 向量索引 - 存储文档向量表示

3. **查询接口**：
   - `query_knowledge.py` - 自然语言查询接口

4. **导出工具**：
   - `export_to_obsidian.py` - 知识图谱到 Obsidian 的导出工具

## 快速开始

请参考 [使用指南](./usage_guide.md) 了解如何部署和使用本系统。

开发者请参考 [开发指南](./develop_guide.md) 了解系统架构和扩展方法。
