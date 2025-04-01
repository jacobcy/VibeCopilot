# VibeCopilot 知识管理系统开发指南

本指南面向希望扩展、定制或深入理解 VibeCopilot 知识管理系统的开发者。

## 系统架构

![知识管理系统架构](../images/km_architecture.png)

VibeCopilot 知识管理系统采用模块化设计，主要由以下组件构成：

### 1. 文档处理层

#### LangChain 解析器 (`langchain_parser.py`)

```
KnowledgeParser
├── __init__()
├── process_documents()
├── extract_entities_and_relations()
├── create_vector_index()
└── load_document()
```

核心功能：

- 文档加载与处理
- 实体和关系提取
- 向量索引创建

#### OpenAI 解析器 (`openai_parser.py`)

传统解析器，直接调用 OpenAI API 实现文档语义理解。

### 2. 存储层

#### Basic Memory 数据库

- 实体存储：文档、概念、标签
- 关系存储：实体间的语义关系
- 观察记录：实体属性和元数据

数据模型：
```
Entity
├── id
├── type
└── attributes

Relation
├── source_id
├── target_id
├── type
└── attributes

Observation
├── entity_id
├── attribute
├── value
└── timestamp
```

#### 向量存储 (FAISS)

使用 FAISS 向量数据库存储文档的向量表示，支持高效的相似度搜索。

### 3. 查询层 (`query_knowledge.py`)

```
KnowledgeQuerier
├── __init__()
├── create_query_chain()
└── query()
```

结合 LangChain 的对话检索链实现自然语言查询。

### 4. 导出层 (`export_to_obsidian.py`)

将 Basic Memory 中的知识图谱导出为 Obsidian 可用的 Markdown 格式。

## 开发指南

### 环境设置

推荐使用虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 扩展指南

#### 1. 添加新的解析器

创建一个继承自基础解析器的新类：

```python
from .base_parser import BaseParser

class YourCustomParser(BaseParser):
    def __init__(self, db_path):
        super().__init__(db_path)
        # 自定义初始化

    def process_documents(self, docs_dir):
        # 自定义文档处理逻辑
        pass

    def extract_entities_and_relations(self, content):
        # 自定义实体和关系提取逻辑
        pass
```

#### 2. 扩展查询功能

修改 `query_knowledge.py` 以支持新的查询类型：

```python
def create_specialized_chain(self):
    # 创建特定领域的查询链
    pass

def domain_specific_query(self, question):
    # 实现特定领域的查询逻辑
    pass
```

#### 3. 添加新的导出格式

创建新的导出器类：

```python
class NewFormatExporter:
    def __init__(self, db_path, output_path):
        self.db_path = db_path
        self.output_path = output_path

    def export(self):
        # 导出逻辑
        pass
```

### 测试指南

建议为每个组件创建单元测试：

```python
import unittest
from scripts.basic_memory.langchain_parser import KnowledgeParser

class TestKnowledgeParser(unittest.TestCase):
    def setUp(self):
        self.parser = KnowledgeParser("/path/to/test/db")

    def test_extract_entities(self):
        content = "测试内容"
        result = self.parser.extract_entities_and_relations(content)
        self.assertIsNotNone(result)
        # 更多断言...
```

运行测试：
```bash
python -m unittest discover tests
```

## 性能优化

### 大规模文档处理

- 考虑使用并行处理: `multiprocessing.Pool`
- 实现增量索引更新
- 对大文档进行分块处理

### 查询性能优化

- 调整向量检索参数: `k` 值和相似度阈值
- 缓存频繁查询结果
- 考虑使用更高效的向量索引方法

## 贡献指南

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## API 参考

详细的 API 文档请参考 [API 文档](./api_reference.md)。
