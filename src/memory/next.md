# 向量知识库实现计划

## 核心目标

实现高效的文档向量存储和语义召回系统，用于存储和检索开发资料。

## 技术方案

采用ChromaDB作为向量数据库后端，具有以下优势：

- 简单易用的API接口
- 内置持久化存储
- 强大的元数据过滤能力
- 通过pip一键安装，无复杂依赖

## 实现路线图

### 一、基础存储层（已完成）

- [x] 定义`VectorStore`抽象接口
- [x] 实现`ChromaVectorStore`核心类
- [x] 开发`BasicMemoryAdapter`适配器
- [x] 支持基本CRUD操作

### 二、功能完善（已完成）

- [x] 修复文档获取功能缺陷
- [x] 解决Langchain导入警告
- [x] 实现批量文档处理优化
- [x] 添加集合统计信息功能
- [x] 改进向量相似度计算

### 三、记忆管理（已完成）

- [x] 实现混合检索（关键词+语义）
- [x] 创建统一的`MemoryManager`类
- [x] 改造memory命令接口
- [x] 实现SQLite与向量库集成
- [x] 开发数据库迁移工具
- [x] 添加记忆统计功能

### 四、语义搜索增强（当前阶段）

- [ ] 添加实体与关系检索功能
- [ ] 实现搜索结果高亮和片段生成
- [ ] 添加相关性反馈机制
- [ ] 支持复杂查询（布尔逻辑、范围过滤）
- [ ] 开发搜索结果聚类功能

### 五、分布式与高性能（下一阶段）

- [ ] 实现记忆数据迁移和清理工具
- [ ] 提供记忆数据统计报告
- [ ] 实现数据分片与并行处理
- [ ] 添加向量索引缓存机制
- [ ] 设计增量更新策略
- [ ] 实现数据备份与恢复
- [ ] 添加基本访问控制

## 已完成功能

1. **文档获取功能修复**
   ```python
   # 解决ChromaDB文档获取问题
   collection.get(
       ids=[doc_id],
       include=["metadatas", "documents", "embeddings"]
   )
   ```

2. **Langchain导入更新**
   ```python
   # 旧导入
   from langchain.vectorstores import Chroma
   from langchain.embeddings import HuggingFaceEmbeddings
   from langchain.docstore.document import Document

   # 新导入
   from langchain_community.vectorstores import Chroma
   from langchain_community.embeddings import HuggingFaceEmbeddings
   from langchain_core.documents import Document
   ```

3. **批量文档处理**
   ```python
   async def batch_store(
       self,
       texts: List[str],
       metadata: Optional[List[Dict[str, Any]]] = None,
       folder: Optional[str] = None,
       batch_size: int = 100
   ) -> List[str]:
       """批量存储文本及元数据到向量库，提高大批量数据处理效率"""
       # ... 实现见ChromaVectorStore类
   ```

4. **混合检索实现**
   ```python
   async def hybrid_search(
       self,
       query: str,
       limit: int = 5,
       filter_dict: Optional[Dict[str, Any]] = None,
       keyword_weight: float = 0.3,
       semantic_weight: float = 0.7,
   ) -> List[Dict[str, Any]]:
       """混合检索，结合语义搜索和关键词搜索"""
       # ... 实现见ChromaVectorStore类
   ```

5. **记忆管理器与SQL集成**
   ```python
   class MemoryManager:
       """整合文档解析和向量存储功能，提供简单的知识记忆存取和召回功能"""

       def __init__(self, config: Optional[Dict[str, Any]] = None):
           # 初始化向量存储和SQLite存储
           self.vector_store = ChromaVectorStore(config=vector_store_config)
           self.session = get_session()
           self.memory_item_repo = MemoryItemRepository(self.session)

       async def store_memory(self, content: str, title: Optional[str] = None,
                             tags: Optional[str] = None, folder: Optional[str] = None) -> Dict[str, Any]:
           """存储记忆，解析内容并存储到向量库和SQLite数据库中"""

       async def retrieve_memory(self, query: str, limit: int = 5) -> Dict[str, Any]:
           """召回记忆，根据查询检索相关记忆，支持SQLite缓存"""

       # ... 其他集成方法
   ```

6. **数据库迁移工具**
   ```python
   def update_memory_item_schema():
       """更新MemoryItem表结构"""
       # 获取数据库引擎
       engine = get_engine()

       # 获取表结构检查器
       inspector = inspect(engine)

       # 定义需要添加的列
       new_columns = []
       if 'permalink' not in columns:
           new_columns.append(Column('permalink', String(255)))
       if 'folder' not in columns:
           new_columns.append(Column('folder', String(100)))
       # ... 添加其他向量库相关字段
   ```

## 现阶段优先任务

1. **实体关系检索增强**
   ```python
   async def retrieve_by_entity_relation(
       self,
       entity_name: Optional[str] = None,
       relation_type: Optional[str] = None,
       limit: int = 5
   ) -> Dict[str, Any]:
       """通过实体和关系检索记忆"""
       # 实现计划
       # 1. 从实体管理器查找匹配的实体
       # 2. 从关系管理器查找匹配的关系
       # 3. 获取关联的记忆源
       # 4. 返回格式化结果
   ```

2. **搜索结果片段生成**
   ```python
   def generate_snippets(
       self,
       query: str,
       document: str,
       window_size: int = 50
   ) -> List[str]:
       # 实现计划
       # 1. 将文档分割成句子
       # 2. 计算每个句子与查询的相关性
       # 3. 选择最相关的句子及其上下文作为片段
       # 4. 高亮匹配的关键词
   ```

3. **相关性反馈机制**
   ```python
   async def search_with_feedback(
       self,
       query: str,
       positive_examples: List[str] = None,
       negative_examples: List[str] = None,
       limit: int = 5
   ) -> Dict[str, Any]:
       """基于用户反馈的搜索，类似于"更多类似这样"或"减少类似这样"的功能"""
       # 实现计划
       # 1. 使用原始查询获取初始结果
       # 2. 根据正面和负面例子调整查询向量
       # 3. 使用调整后的向量重新搜索
       # 4. 重新排序搜索结果
   ```

## 技术依赖

- **ChromaDB**: 向量数据库
- **Langchain**: 向量存储抽象层
- **SQLAlchemy**: 关系数据库ORM
- **HuggingFace**: 文本嵌入模型
- **sentence-transformers**: 默认嵌入模型
- **LLM解析器**: 用于提取实体和关系

## 使用示例

```python
# 初始化记忆管理器
memory_manager = MemoryManager()

# 存储记忆
result = await memory_manager.store_memory(
    content="人工智能是计算机科学的一个分支，它研究如何使计算机能够像人一样思考和学习。",
    title="AI简介",
    tags="AI,技术,计算机科学",
    folder="knowledge"
)

# 检索记忆
memories = await memory_manager.retrieve_memory("计算机如何学习")

# 获取特定记忆
memory = await memory_manager.get_memory_by_id("memory://knowledge/1234-5678")

# 从SQLite通过ID获取
memory_item = memory_item_repo.get_by_id(123)

# 列出所有记忆
all_memories = await memory_manager.list_memories(folder="knowledge")

# 删除记忆
await memory_manager.delete_memory("memory://knowledge/1234-5678")
```

## memory命令设计

提供以下命令用于管理知识记忆：

1. **`/memory store`**: 存储新知识
   - 参数: `--content`, `--title`, `--tags`, `--folder`
   - 示例: `/memory store --content "Python是一种高级编程语言" --title "Python简介" --tags "编程,语言" --folder "languages"`

2. **`/memory search`**: 搜索记忆
   - 参数: `--query`, `--limit`
   - 示例: `/memory search --query "编程语言特点" --limit 3`

3. **`/memory get`**: 获取特定记忆
   - 参数: `--id` (记忆链接或ID)
   - 示例: `/memory get --id "memory://knowledge/1234-5678"` 或 `/memory get --id 123`

4. **`/memory list`**: 列出所有记忆
   - 参数: `--folder`, `--limit`, `--tags`
   - 示例: `/memory list --tags "编程" --limit 10 --folder "languages"`

5. **`/memory delete`**: 删除记忆
   - 参数: `--id` (记忆链接或ID), `--force`
   - 示例: `/memory delete --id "memory://knowledge/1234-5678"` 或 `/memory delete --id 123 --force`

6. **`/memory update`**: 更新记忆
   - 参数: `--id`, `--content`, `--tags`
   - 示例: `/memory update --id 123 --content "新内容" --tags "新标签"`

7. **`/memory check`**: 测试知识库连接
   - 示例: `/memory check`

## 下一步开发计划 (2024年Q2)

1. **实体与关系检索增强**
   - 完成实体关系检索API
   - 改进实体和关系提取精度
   - 添加实体关系可视化功能

2. **搜索结果优化**
   - 实现搜索结果高亮功能
   - 开发智能摘要和片段生成
   - 添加结果聚类和分类功能

3. **交互体验提升**
   - 开发记忆推荐功能
   - 实现相关性反馈机制
   - 支持复杂查询语法

4. **性能优化**
   - 优化大规模记忆存储性能
   - 实现查询缓存机制
   - 改进向量计算效率

5. **自测与评估**
   - 设计检索质量评估指标
   - 实现自动性能基准测试
   - 构建示例数据集和测试用例
