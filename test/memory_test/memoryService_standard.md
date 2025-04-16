
# MemoryService标准规范文档

## 1. 概述

`MemoryService`是VibeCopilot知识库服务的统一接口，它封装了所有与知识库交互的功能，为命令行工具和其他模块提供了一致的API。本文档定义了使用本地向量存储架构实现`MemoryService`的标准规范。

## 2. 服务架构

### 2.1 三层架构设计

任何`MemoryService`实现都应遵循以下三层架构：

1. **接口层**：提供统一的API接口，隐藏内部实现细节
2. **服务层**：实现具体业务逻辑，可按功能划分为多个子服务
3. **存储层**：负责数据持久化和检索，支持本地向量存储

### 2.2 核心组件

- **MemoryService**：门面(Facade)模式实现，对外提供统一接口
- **向量存储引擎**：负责存储和检索向量数据
- **数据同步机制**：确保本地存储与远程系统(如有)保持一致

## 3. 接口规范

### 3.1 基本接口

所有`MemoryService`实现必须支持以下核心接口：

```python
class MemoryService:
    # 笔记管理功能
    def create_note(self, content: str, title: str, folder: str,
                   tags: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]: ...

    def read_note(self, path: str) -> Tuple[bool, str, Dict[str, Any]]: ...

    def update_note(self, path: str, content: str,
                   tags: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]: ...

    def delete_note(self, path: str, force: bool = False) -> Tuple[bool, str, Dict[str, Any]]: ...

    # 搜索功能
    def list_notes(self, folder: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]: ...

    def search_notes(self, query: str,
                    content_type: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]: ...

    # 同步功能
    def sync_all(self) -> Tuple[bool, str, Dict[str, Any]]: ...

    def start_sync_watch(self) -> Tuple[bool, str, Dict[str, Any]]: ...

    def import_documents(self, source_dir: str,
                        recursive: bool = False) -> Tuple[bool, str, Dict[str, Any]]: ...

    def export_documents(self, output_dir: Optional[str] = None,
                        format_type: str = "md") -> Tuple[bool, str, Dict[str, Any]]: ...

    # 统计功能
    def get_memory_stats(self) -> Dict[str, Any]: ...
```

### 3.2 返回格式标准

所有接口返回应遵循以下标准格式：

- **成功/失败标志**：布尔值，表示操作是否成功
- **消息**：字符串，描述操作结果
- **数据**：字典或列表，包含操作的具体结果数据

## 4. 向量存储实现指南

### 4.1 向量存储配置

```python
# 向量存储配置示例
vector_config = {
    "vector_db_path": "/path/to/vector/store",
    "embedding_model": "text-embedding-3-small",  # 或其他本地模型
    "vector_dimensions": 1536,  # 根据实际模型调整
    "distance_metric": "cosine",  # 余弦相似度
    "index_type": "flat"   # 或 "hnsw", "ivf" 等
}
```

### 4.2 向量存储接口

本地向量存储实现应提供以下基本功能：

```python
class VectorStoreInterface:
    def add_item(self, id: str, text: str, metadata: Dict[str, Any]) -> None: ...
    def get_item(self, id: str) -> Optional[Dict[str, Any]]: ...
    def update_item(self, id: str, text: str, metadata: Dict[str, Any]) -> None: ...
    def delete_item(self, id: str) -> None: ...
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]: ...
    def list_items(self, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]: ...
```

### 4.3 向量检索性能要求

- 搜索延迟：小于500ms（对于1000条记录）
- 更新延迟：小于200ms
- 内存使用：根据数据量合理规划
- 支持增量更新和部分更新

## 5. 内存服务实现示例

```python
class LocalVectorMemoryService(MemoryService):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.vector_store = self._init_vector_store()
        self.metadata_store = self._init_metadata_store()
        self.logger = logging.getLogger(__name__)

    def _init_vector_store(self):
        # 初始化本地向量存储
        # 可以使用FAISS, Annoy, Hnswlib, Chroma等库实现
        pass

    def _init_metadata_store(self):
        # 初始化元数据存储
        # 可以使用SQLite或其他轻量级数据库
        pass

    # 实现MemoryService定义的所有方法...
```

## 6. 测试规范

所有`MemoryService`实现应通过以下测试：

### 6.1 单元测试

```bash
# 运行单元测试示例
cd test/memory_test
python test_memory_cmd.py
```

### 6.2 性能测试

```bash
# 运行性能测试示例
cd test/memory_test
./quick_test.sh
```

### 6.3 兼容性测试

确保与现有CLI命令和API调用完全兼容：

```bash
# 手动测试示例
cd test/memory_test
./manual_test.sh
```

## 7. 集成指南

### 7.1 替换现有服务

要替换当前的`MemoryService`实现：

1. 创建新的向量存储服务类，实现所有必需接口
2. 更新`src/memory/__init__.py`，导出新的服务实现
3. 确保CLI命令和其他依赖模块不需要修改

### 7.2 配置示例

```python
# 配置文件示例
{
    "vector_store": {
        "type": "local",  # 或 "faiss", "chroma" 等
        "path": "./data/vectors",
        "embedding_model": "local-model-name",
        "dimensions": 1536
    },
    "metadata_store": {
        "type": "sqlite",
        "path": "./data/metadata.db"
    },
    "sync": {
        "enabled": true,
        "interval": 300  # 秒
    }
}
```

## 8. 性能优化建议

1. 使用批量操作减少数据库交互
2. 实现向量缓存减少计算开销
3. 考虑使用异步处理大批量文档
4. 优化向量索引结构，如使用HNSW替代暴力搜索
5. 定期执行索引优化和清理
