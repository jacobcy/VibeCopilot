# VibeCopilot Memory 系统架构规范

## 1. 系统概述

VibeCopilot Memory 系统是一个灵活、可扩展的知识库管理系统，为用户提供知识存储、检索和管理能力。`MemoryService` 是其核心组件，作为统一接口，封装了所有与知识库交互的功能，为命令行工具和其他模块提供了一致的 API。本文档定义了完整的 Memory 系统架构规范，适用于使用、扩展和替换 Memory 系统组件的开发者。

## 2. 架构设计

### 2.1 三层架构设计

Memory 系统遵循以下三层架构：

1. **接口层**：提供统一的 API 接口，隐藏内部实现细节
2. **服务层**：实现具体业务逻辑，可按功能划分为多个子服务
3. **存储层**：负责数据持久化和检索，支持可插拔的后端存储实现

### 2.2 核心组件

- **MemoryService**：门面(Facade)模式实现，对外提供统一接口，屏蔽后端差异
- **Memory 后端插件**：可互换的后端实现，如 ChromaDB、FAISS 或文件系统等
- **关系数据库存储**：存储结构化元数据，如 SQLite
- **向量数据库存储**：存储文本嵌入和执行语义搜索
- **SyncOrchestrator**：负责编排同步流程，决定同步什么和如何处理，调用MemoryService的方法执行实际存储
- **SyncExecutor**：在MemoryService内部，专注于执行存储操作，由MemoryService调用

### 2.3 系统角色与职责

#### MemoryService 角色

`MemoryService` 作为统一的外观（Facade），在 Memory 系统中扮演以下角色：

1. **接口统一**：
   - 提供统一 API，向应用其他部分提供稳定的接口，屏蔽后端差异
   - 维护 API 契约，确保即使后端更改，API 契约也保持稳定

2. **预处理与验证**：
   - 输入验证：验证调用方提供的参数符合要求
   - 路径规范化：规范化 folder 路径，然后再传递给后端
   - 参数转换：必要时进行参数转换和格式调整

3. **后端委托**：
   - 后端选择：根据配置选择和初始化适当的后端插件
   - 请求委托：将验证和预处理后的请求委托给选定的后端
   - 响应处理：处理后端响应，确保返回格式一致

4. **错误处理**：
   - 异常捕获：捕获后端可能抛出的异常
   - 统一错误格式：将各种错误转换为一致的返回格式
   - 提供上下文：在错误消息中添加必要的上下文信息

#### 后端插件职责

Memory 后端插件实现应当严格遵循以下职责边界：

1. **技术封装**：
   - 完全封装底层技术细节：例如 ChromaDB、FAISS、文件系统的特定 API 和行为
   - 自主处理存储：负责所有数据的存储、索引维护和检索
   - 资源管理：管理连接池、缓存和其他资源，确保高效和安全的资源使用

2. **接口实现**：
   - 完整实现定义接口：实现所规定的 `MemoryBackendBase` 所定义的所有必要方法
   - 保持签名一致：方法签名应符合接口定义，以确保可替换性
   - 遵循返回格式：所有方法必须返回 `(success, message, data)` 三元组

3. **标准遵循**：
   - 遵循 permalink 标准：按照定义生成、解析和管理 permalink
   - 遵循 folder 标准：正确处理 folder 组织结构
   - 数据格式一致：确保返回的数据结构与其他后端一致，以便 `MemoryService` 可以统一处理

4. **错误处理**：
   - 包装特定错误：将特定于技术的错误转换为统一的错误形式
   - 提供清晰消息：错误消息应清晰表明问题所在
   - 适当的日志：记录关键操作和错误，方便故障排查

## 3. MemoryService 接口规范

### 3.1 基本接口

所有 `MemoryService` 实现必须支持以下核心接口：

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

    # 同步功能 - 仅提供接口，不实现具体同步逻辑
    def sync_all(self) -> Tuple[bool, str, Dict[str, Any]]:
        """提供同步接口，实际同步逻辑由SyncOrchestrator负责执行"""

    def execute_storage(self, texts: List[str], metadata_list: List[Dict[str, Any]],
                      collection_name: str) -> List[str]:
        """执行存储操作，由SyncOrchestrator调用"""

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

示例：
```python
# 成功返回
return True, "笔记创建成功", {"id": 123, "permalink": "memory://folder/title"}

# 失败返回
return False, "笔记创建失败：标题已存在", {}
```

## 4. Memory 后端插件接口

所有 Memory 后端实现必须遵循以下接口契约，这些方法将被 `MemoryService` 调用：

```python
class MemoryBackendBase:
    """Memory 后端基类，定义了所有后端必须实现的接口"""

    def create_note(self, title: str, content: str, folder: str, tags: Optional[str] = None, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
        """创建笔记

        Args:
            title: 笔记标题
            content: 笔记内容
            folder: 规范化的文件夹路径
            tags: 可选的标签（逗号分隔的字符串）
            **kwargs: 额外参数

        Returns:
            Tuple[bool, str, Dict[str, Any]]: (成功标志, 消息, 数据字典)
            数据字典必须包含 'permalink' 键
        """
        raise NotImplementedError

    def read_note(self, path: str, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
        """读取笔记

        Args:
            path: 笔记路径或永久链接
            **kwargs: 额外参数

        Returns:
            Tuple[bool, str, Dict[str, Any]]: (成功标志, 消息, 笔记数据)
        """
        raise NotImplementedError

    def update_note(self, path: str, content: Optional[str] = None, title: Optional[str] = None,
                   folder: Optional[str] = None, tags: Optional[str] = None, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
        """更新笔记

        Args:
            path: 笔记路径或永久链接
            content: 可选的新内容
            title: 可选的新标题
            folder: 可选的新文件夹（已规范化）
            tags: 可选的新标签
            **kwargs: 额外参数

        Returns:
            Tuple[bool, str, Dict[str, Any]]: (成功标志, 消息, 更新后的数据)
        """
        raise NotImplementedError

    def delete_note(self, path: str, force: bool = False, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
        """删除笔记

        Args:
            path: 笔记路径或永久链接
            force: 是否强制删除
            **kwargs: 额外参数

        Returns:
            Tuple[bool, str, Dict[str, Any]]: (成功标志, 消息, 额外数据)
        """
        raise NotImplementedError

    def list_notes(self, folder: Optional[str] = None, **kwargs) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """列出笔记

        Args:
            folder: 可选的文件夹过滤（已规范化）
            **kwargs: 额外参数

        Returns:
            Tuple[bool, str, List[Dict[str, Any]]]: (成功标志, 消息, 笔记列表)
        """
        raise NotImplementedError

    def search_notes(self, query: str, folder: Optional[str] = None, **kwargs) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """搜索笔记

        Args:
            query: 搜索查询
            folder: 可选的文件夹范围（已规范化）
            **kwargs: 额外参数

        Returns:
            Tuple[bool, str, List[Dict[str, Any]]]: (成功标志, 消息, 结果列表)
            结果应当包含相关度分数
        """
        raise NotImplementedError

    def sync_all(self, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
        """同步知识库（若支持）

        Args:
            **kwargs: 额外参数

        Returns:
            Tuple[bool, str, Dict[str, Any]]: (成功标志, 消息, 同步结果)
        """
        # 这个方法可选，不是所有后端都需要同步功能
        return True, "同步不适用于此后端", {}

    def import_documents(self, source_dir: str, recursive: bool = False, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
        """导入文档（若支持）

        Args:
            source_dir: 源目录
            recursive: 是否递归处理子目录
            **kwargs: 额外参数

        Returns:
            Tuple[bool, str, Dict[str, Any]]: (成功标志, 消息, 导入结果)
        """
        # 这个方法可选，不是所有后端都需要导入功能
        return False, "此后端不支持文档导入", {}
```

## 5. 数据处理标准

### 5.1 permalink 处理标准

`permalink` 是 Memory 系统的核心概念，是每个记忆项的唯一标识符。所有后端实现必须遵循以下标准：

#### 5.1.1 permalink 格式规范

- **标准格式**：`memory://<folder_path>/<title>`
  - 例如：`memory://projects/VibeCopilot/API设计`
  - 或者：`memory://日记/2023/今天的感想`

- **替代格式**：允许后端使用基于 UUID 的格式，但必须在内部映射回用户友好的路径
  - 例如：`memory://uuid/550e8400-e29b-41d4-a716-446655440000`

#### 5.1.2 permalink 生成职责

- **生成时机**：后端插件必须在创建新记忆项时生成 permalink
- **返回方式**：后端的 `create_note` 方法必须在返回的数据字典中包含 `permalink` 键
- **唯一性保证**：后端负责确保生成的 permalink 在其存储范围内唯一

#### 5.1.3 permalink 解析与映射

- **解析责任**：后端插件负责解析传入的 permalink，并将其映射到内部存储结构
  - 例如：ChromaDB 后端可能将 permalink 映射到内部 ID
  - FAISS 后端可能将 permalink 映射到向量索引位置
  - 文件系统后端可能将 permalink 映射到文件路径

- **标准化**：后端应能处理不同形式的路径引用，包括：
  - 完整 permalink: `memory://folder/title`
  - 相对路径: `folder/title`
  - 仅标题 (当上下文明确时): `title`

#### 5.1.4 permalink 一致性要求

- **跨后端一致性**：所有后端必须以相同的方式理解 permalink 格式
- **持久性**：一旦生成，permalink 应保持稳定，即使底层存储发生变化
- **唯一映射**：每个 permalink 必须唯一映射到一个资源，不允许一对多映射

### 5.2 folder 处理标准

`folder` 作为组织记忆项的逻辑命名空间，其处理也需要标准化：

#### 5.2.1 folder 语义定义

- **逻辑命名空间**：folder 是一个逻辑概念，用于组织记忆项
- **内部实现自由**：后端可以自由选择如何在其存储中实现这种组织
  - 例如：通过元数据标记、目录结构、ID前缀、集合划分等

#### 5.2.2 folder 路径规范化

- **初步规范化**：`MemoryService` 在调用后端前负责初步规范化，包括：
  - 统一路径分隔符为 `/`
  - 移除首尾的斜杠
  - 处理空格和特殊字符
  - 例如：`/  Projects\\VibeCopilot  /` → `Projects/VibeCopilot`

- **后端责任**：后端接收规范化后的 folder 路径，不应再执行与用户界面相关的规范化
  - 后端可以进行内部必要的技术调整（例如，转义特殊字符以适应其存储系统）

#### 5.2.3 folder 层级支持

- **层级表示**：使用 `/` 作为分隔符表示层级结构
  - 例如：`项目/VibeCopilot/设计文档`

- **层级行为标准**：
  - 列举一个文件夹内容时应仅返回该层级的直接子项
  - 支持遍历树形结构获取完整层级内容
  - 搜索时支持限定在特定文件夹及其子文件夹范围内

## 6. 向量存储实现指南

### 6.1 向量存储配置

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

### 6.2 向量存储接口

本地向量存储实现应提供以下基本功能：

```python
class VectorStoreInterface:
    def add_item(self, id: str, text: str, metadata: Dict[str, Any]) -> None: ...
    def get_item(self, id: str) -> Optional[Dict[str, Any]]: ...
    def update_item(self, id: str, text: str, metadata: Dict[str, Any]) -> None: ...
    def delete_note(self, id: str) -> None: ...
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]: ...
    def list_items(self, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]: ...
```

### 6.3 向量检索性能要求

- 搜索延迟：小于500ms（对于1000条记录）
- 更新延迟：小于200ms
- 内存使用：根据数据量合理规划
- 支持增量更新和部分更新

## 7. 测试规范

所有 `MemoryService` 和后端插件实现应通过以下测试：

### 7.1 单元测试

```bash
# 运行单元测试示例
cd test/memory_test
python test_memory_cmd.py
```

### 7.2 性能测试

```bash
# 运行性能测试示例
cd test/memory_test
./quick_test.sh
```

### 7.3 兼容性测试

确保与现有CLI命令和API调用完全兼容：

```bash
# 手动测试示例
cd test/memory_test
./manual_test.sh
```

### 7.4 标准遵循测试

确保实现遵循所有规定的标准，特别是：

- permalink 格式和处理
- folder 处理和层级支持
- 错误处理和报告

## 8. 集成与配置

### 8.1 环境变量配置

```
# 在 .env 文件中配置后端类型和参数
MEMORY_BACKEND_TYPE=chroma  # 或 faiss, file, sqlite 等
MEMORY_BACKEND_CONFIG='{"path": "/path/to/storage", "other_option": "value"}'
```

### 8.2 代码中的后端初始化

```python
# src/memory/__init__.py 或类似文件
from typing import Dict, Any, Optional

from src.memory.backends.chroma_backend import ChromaMemoryBackend
from src.memory.backends.faiss_backend import FaissMemoryBackend
from src.memory.backends.file_backend import FileMemoryBackend
# ... 其他后端导入

class MemoryService:
    """Memory服务，作为后端的Facade"""

    _instance = None  # 单例实例

    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        # 单例模式实现
        if cls._instance is None:
            cls._instance = super(MemoryService, cls).__new__(cls)
            cls._instance._init_backend(config)
        return cls._instance

    def _init_backend(self, config: Optional[Dict[str, Any]] = None):
        """初始化后端"""
        import os
        import json

        # 获取配置
        backend_type = os.getenv("MEMORY_BACKEND_TYPE", "chroma").lower()
        backend_config = config or {}

        env_config = os.getenv("MEMORY_BACKEND_CONFIG", "{}")
        if env_config:
            try:
                env_config_dict = json.loads(env_config)
                backend_config.update(env_config_dict)
            except json.JSONDecodeError:
                pass

        # 根据类型选择后端
        if backend_type == "chroma":
            self.backend = ChromaMemoryBackend(**backend_config)
        elif backend_type == "faiss":
            self.backend = FaissMemoryBackend(**backend_config)
        elif backend_type == "file":
            self.backend = FileMemoryBackend(**backend_config)
        # ... 其他后端类型
        else:
            raise ValueError(f"不支持的后端类型: {backend_type}")
```

### 8.3 替换现有服务

要替换当前的 `MemoryService` 实现：

1. 创建新的向量存储服务类，实现所有必需接口
2. 更新 `src/memory/__init__.py`，导出新的服务实现
3. 确保CLI命令和其他依赖模块不需要修改

### 8.4 切换后端步骤

1. 修改环境变量 `MEMORY_BACKEND_TYPE` 为新的后端类型
2. 可选: 提供必要的后端特定配置
3. 重启应用或重新初始化 `MemoryService`

### 8.5 同步系统架构

同步系统遵循以下架构设计：

1. **SyncOrchestrator**（编排层）：
   - 位于src/sync目录
   - 负责决定什么需要同步，如何处理文件
   - 调用处理器处理文件内容
   - 调用MemoryService的execute_storage方法执行存储

2. **MemoryService**（接口层）：
   - 仅提供标准存储接口
   - 不参与同步逻辑的编排和决策
   - 通过execute_storage方法执行具体的存储操作
   - 内部改变不影响外部同步系统

3. **SyncExecutor**（执行层）：
   - 位于src/memory目录
   - 专注于执行存储操作
   - 由MemoryService调用，不直接与SyncOrchestrator交互

## 9. 性能优化建议

1. **批量操作**：使用批量操作减少数据库交互
2. **向量缓存**：实现向量缓存减少计算开销
3. **异步处理**：考虑使用异步处理大批量文档
4. **索引优化**：优化向量索引结构，如使用HNSW替代暴力搜索
5. **定期维护**：定期执行索引优化和清理
6. **内存管理**：对大型向量集合实现分段加载或内存映射
7. **预计算**：对频繁访问的查询进行预计算和缓存

## 10. Repository与后端插件的关系

为明确系统各层的职责，特别说明Repository层与后端插件的关系：

### 10.1 Repository职责

- `MemoryItemRepository` 仅负责 `MemoryItem` 模型在关系数据库（SQLite）中的持久化操作
- 它不应调用任何后端插件或 `chroma_utils` 等向量存储工具
- 所有结构化数据（元数据）存储和检索都通过Repository完成

### 10.2 后端插件职责

- 后端插件负责非结构化数据的存储（内容、向量等）
- 管理permalink和内部ID的映射
- 执行向量检索和语义搜索

### 10.3 MemoryService协调

- `MemoryService` 协调Repository和后端插件的交互
- 维护结构化数据与向量数据的一致性
- 在合适的时机调用Repository或后端插件的方法

### 10.4 架构图

```
用户接口 / API
    |
    v
MemoryService (外观模式)
   /        \
  v          v
Repository    后端插件
  |            |
  v            v
SQLite      向量存储
(元数据)    (内容/向量)
```

## 11. 同步系统与Memory系统的责任分离

为确保系统模块化和可维护性，Memory系统与同步系统的责任应明确分离：

1. **Memory系统职责**：
   - 提供统一的存储和检索接口
   - 执行存储操作（但不决定什么需要存储）
   - 维护结构化和非结构化数据的一致性

2. **同步系统职责**：
   - 监控文件变化
   - 决定哪些文件需要同步
   - 处理不同类型的文件内容
   - 编排同步流程
   - 调用Memory系统执行存储

这种分离确保Memory系统内部的任何改变都不会影响同步系统，同时同步系统也可以独立演化而不影响Memory的核心功能。

---

遵循本文档中的架构标准和开发规范，您可以实现、扩展或替换VibeCopilot Memory系统的各个组件，确保它们能够无缝协作并提供一致的用户体验。
