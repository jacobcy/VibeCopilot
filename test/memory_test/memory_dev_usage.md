# MemoryService 开发者使用指南

本文档展示如何在Python代码中直接使用`MemoryService`接口进行知识库操作，适用于需要在其他模块或服务中集成知识库功能的开发者。

## 基本使用

### 导入MemoryService

首先，从`src.memory`模块导入`MemoryService`类：

```python
from src.memory import MemoryService

# 创建MemoryService实例
memory_service = MemoryService()
```

### 创建笔记

```python
def create_example_note():
    # 准备数据
    title = "API使用示例"
    folder = "dev_examples"
    content = "# 这是通过API创建的笔记\n\n使用MemoryService接口可以轻松创建笔记。"
    tags = "API,示例,开发"

    # 调用API创建笔记
    success, message, data = memory_service.create_note(
        content=content,
        title=title,
        folder=folder,
        tags=tags
    )

    # 处理结果
    if success:
        print(f"笔记创建成功: {message}")
        return data.get("permalink")  # 返回笔记的永久链接
    else:
        print(f"笔记创建失败: {message}")
        return None
```

### 读取笔记

```python
def read_note_example(path):
    # 调用API读取笔记
    success, message, data = memory_service.read_note(path=path)

    # 处理结果
    if success:
        print(f"笔记标题: {data.get('title')}")
        print(f"笔记内容: {data.get('content')[:100]}...")  # 显示前100个字符
        print(f"创建时间: {data.get('created_at')}")
        return data
    else:
        print(f"读取笔记失败: {message}")
        return None
```

### 更新笔记

```python
def update_note_example(path, new_content):
    # 调用API更新笔记
    success, message, data = memory_service.update_note(
        path=path,
        content=new_content
    )

    # 处理结果
    if success:
        print(f"笔记更新成功: {message}")
        return True
    else:
        print(f"笔记更新失败: {message}")
        return False
```

### 删除笔记

```python
def delete_note_example(path):
    # 调用API删除笔记
    success, message, data = memory_service.delete_note(
        path=path,
        force=True  # 强制删除，不提示确认
    )

    # 处理结果
    if success:
        print(f"笔记删除成功: {message}")
        return True
    else:
        print(f"笔记删除失败: {message}")
        return False
```

## 搜索和列表

### 列出笔记

```python
def list_notes_example(folder=None):
    # 调用API列出笔记
    success, message, data = memory_service.list_notes(folder=folder)

    # 处理结果
    if success:
        print(f"找到 {len(data)} 个笔记:")
        for idx, note in enumerate(data, 1):
            print(f"{idx}. {note.get('title')} ({note.get('folder')})")
        return data
    else:
        print(f"列出笔记失败: {message}")
        return []
```

### 搜索笔记

```python
def search_notes_example(query):
    # 调用API搜索笔记
    success, message, data = memory_service.search_notes(query=query)

    # 处理结果
    if success:
        print(f"搜索'{query}'找到 {len(data)} 个结果:")
        for idx, note in enumerate(data, 1):
            print(f"{idx}. {note.get('title')} (相关度: {note.get('score', 'N/A')})")
        return data
    else:
        print(f"搜索笔记失败: {message}")
        return []
```

## 同步和导入导出

### 同步知识库

```python
def sync_memory_example():
    # 调用API同步知识库
    success, message, data = memory_service.sync_all()

    # 处理结果
    if success:
        print(f"知识库同步成功: {message}")
        if data:
            print(f"同步详情: {data}")
        return True
    else:
        print(f"知识库同步失败: {message}")
        return False
```

### 导入文档

```python
def import_documents_example(source_dir):
    # 调用API导入文档
    success, message, data = memory_service.import_documents(
        source_dir=source_dir,
        recursive=True  # 递归导入子目录
    )

    # 处理结果
    if success:
        print(f"文档导入成功: {message}")
        if data and "imported_count" in data:
            print(f"共导入 {data['imported_count']} 个文档")
        return True
    else:
        print(f"文档导入失败: {message}")
        return False
```

## 完整示例

下面是一个将上述功能组合起来的完整示例：

```python
from src.memory import MemoryService

def memory_service_demo():
    # 创建MemoryService实例
    memory_service = MemoryService()

    # 创建笔记
    title = "API完整示例"
    folder = "dev_examples"
    content = "# MemoryService API示例\n\n这是一个完整的API使用示例。"
    tags = "API,示例,完整"

    print("1. 创建笔记...")
    success, message, data = memory_service.create_note(
        content=content,
        title=title,
        folder=folder,
        tags=tags
    )

    if not success:
        print(f"创建笔记失败: {message}")
        return

    path = f"{folder}/{title}"
    print(f"笔记创建成功: {path}")

    # 读取笔记
    print("\n2. 读取笔记...")
    success, message, data = memory_service.read_note(path=path)
    if success:
        print(f"笔记内容: {data.get('content')}")

    # 更新笔记
    print("\n3. 更新笔记...")
    updated_content = f"{content}\n\n## 更新\n\n这是更新后的内容。"
    success, message, _ = memory_service.update_note(
        path=path,
        content=updated_content
    )
    print(f"更新结果: {message}")

    # 搜索笔记
    print("\n4. 搜索笔记...")
    success, message, results = memory_service.search_notes(query="API示例")
    if success and results:
        print(f"找到 {len(results)} 个相关笔记")

    # 删除测试笔记
    print("\n5. 删除笔记...")
    success, message, _ = memory_service.delete_note(path=path, force=True)
    print(f"删除结果: {message}")

    print("\n演示完成.")

if __name__ == "__main__":
    memory_service_demo()
```

## 错误处理最佳实践

使用`MemoryService`时，建议以下错误处理方法：

```python
def safe_memory_operation(operation_name, operation_func, *args, **kwargs):
    """安全执行内存操作，带错误处理"""
    try:
        success, message, data = operation_func(*args, **kwargs)
        if not success:
            print(f"{operation_name}失败: {message}")
            return None
        return data
    except Exception as e:
        print(f"{operation_name}出错: {str(e)}")
        return None

# 使用示例
note_data = safe_memory_operation(
    "读取笔记",
    memory_service.read_note,
    path="folder/title"
)
```

## 注意事项

1. `MemoryService`是单例模式，可以在应用的不同部分共享同一个实例
2. 所有方法都返回三元组 `(success, message, data)`，确保始终检查`success`值
3. 对于批量操作，考虑使用异步处理或分批处理，避免阻塞主线程
4. 在处理大量数据时，可以使用流式处理方法
5. 接口设计遵循了一致性原则，所有方法返回格式相同

---

# Memory 后端开发标准

本部分针对希望开发新的 Memory 后端插件的开发者，定义了一系列标准和规范，确保不同的后端实现（如 ChromaDB、FAISS 或其他）可以无缝替换并与 `MemoryService` 协同工作。

## Memory 后端插件接口

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

## permalink 处理标准

`permalink` 是 Memory 系统的核心概念，是每个记忆项的唯一标识符。所有后端实现必须遵循以下标准：

### 1. permalink 格式规范

- **标准格式**：`memory://<folder_path>/<title>`
  - 例如：`memory://projects/VibeCopilot/API设计`
  - 或者：`memory://日记/2023/今天的感想`

- **替代格式**：允许后端使用基于 UUID 的格式，但必须在内部映射回用户友好的路径
  - 例如：`memory://uuid/550e8400-e29b-41d4-a716-446655440000`

### 2. permalink 生成职责

- **生成时机**：后端插件必须在创建新记忆项时生成 permalink
- **返回方式**：后端的 `create_note` 方法必须在返回的数据字典中包含 `permalink` 键
- **唯一性保证**：后端负责确保生成的 permalink 在其存储范围内唯一

### 3. permalink 解析与映射

- **解析责任**：后端插件负责解析传入的 permalink，并将其映射到内部存储结构
  - 例如：ChromaDB 后端可能将 permalink 映射到内部 ID
  - FAISS 后端可能将 permalink 映射到向量索引位置
  - 文件系统后端可能将 permalink 映射到文件路径

- **标准化**：后端应能处理不同形式的路径引用，包括：
  - 完整 permalink: `memory://folder/title`
  - 相对路径: `folder/title`
  - 仅标题 (当上下文明确时): `title`

### 4. permalink 一致性要求

- **跨后端一致性**：所有后端必须以相同的方式理解 permalink 格式
- **持久性**：一旦生成，permalink 应保持稳定，即使底层存储发生变化
- **唯一映射**：每个 permalink 必须唯一映射到一个资源，不允许一对多映射

## folder 处理标准

`folder` 作为组织记忆项的逻辑命名空间，其处理也需要标准化：

### 1. folder 语义定义

- **逻辑命名空间**：folder 是一个逻辑概念，用于组织记忆项
- **内部实现自由**：后端可以自由选择如何在其存储中实现这种组织
  - 例如：通过元数据标记、目录结构、ID前缀、集合划分等

### 2. folder 路径规范化

- **初步规范化**：`MemoryService` 在调用后端前负责初步规范化，包括：
  - 统一路径分隔符为 `/`
  - 移除首尾的斜杠
  - 处理空格和特殊字符
  - 例如：`/  Projects\\VibeCopilot  /` → `Projects/VibeCopilot`

- **后端责任**：后端接收规范化后的 folder 路径，不应再执行与用户界面相关的规范化
  - 后端可以进行内部必要的技术调整（例如，转义特殊字符以适应其存储系统）

### 3. folder 层级支持

- **层级表示**：使用 `/` 作为分隔符表示层级结构
  - 例如：`项目/VibeCopilot/设计文档`

- **层级行为标准**：
  - 列举一个文件夹内容时应仅返回该层级的直接子项
  - 支持遍历树形结构获取完整层级内容
  - 搜索时支持限定在特定文件夹及其子文件夹范围内

## 后端插件职责

后端插件实现应当严格遵循以下职责边界：

### 1. 技术封装

- **完全封装底层技术细节**：例如 ChromaDB、FAISS、文件系统的特定 API 和行为
- **自主处理存储**：负责所有数据的存储、索引维护和检索
- **资源管理**：管理连接池、缓存和其他资源，确保高效和安全的资源使用

### 2. 接口实现

- **完整实现定义接口**：实现前述的 `MemoryBackendBase` 所定义的所有必要方法
- **保持签名一致**：方法签名应符合接口定义，以确保可替换性
- **遵循返回格式**：所有方法必须返回 `(success, message, data)` 三元组

### 3. 标准遵循

- **遵循 permalink 标准**：按照定义生成、解析和管理 permalink
- **遵循 folder 标准**：正确处理 folder 组织结构
- **数据格式一致**：确保返回的数据结构与其他后端一致，以便 `MemoryService` 可以统一处理

### 4. 错误处理

- **包装特定错误**：将特定于技术的错误转换为统一的错误形式
- **提供清晰消息**：错误消息应清晰表明问题所在
- **适当的日志**：记录关键操作和错误，方便故障排查

## MemoryService 角色

`MemoryService` 作为统一的外观（Facade），在 Memory 系统中扮演以下角色：

### 1. 接口统一

- **提供统一 API**：向应用其他部分提供稳定的接口，屏蔽后端差异
- **维护 API 契约**：确保即使后端更改，API 契约也保持稳定

### 2. 预处理与验证

- **输入验证**：验证调用方提供的参数符合要求
- **路径规范化**：规范化 folder 路径，然后再传递给后端
- **参数转换**：必要时进行参数转换和格式调整

### 3. 后端委托

- **后端选择**：根据配置选择和初始化适当的后端插件
- **请求委托**：将验证和预处理后的请求委托给选定的后端
- **响应处理**：处理后端响应，确保返回格式一致

### 4. 错误处理

- **异常捕获**：捕获后端可能抛出的异常
- **统一错误格式**：将各种错误转换为一致的返回格式
- **提供上下文**：在错误消息中添加必要的上下文信息

## 配置与后端切换

通过配置可以轻松切换不同的 Memory 后端实现：

### 1. 环境变量配置

```
# 在 .env 文件中
MEMORY_BACKEND_TYPE=chroma  # 或 faiss, file, sqlite 等
MEMORY_BACKEND_CONFIG='{"path": "/path/to/storage", "other_option": "value"}'
```

### 2. 代码中的后端初始化

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

### 3. 切换后端的步骤

1. 修改环境变量 `MEMORY_BACKEND_TYPE` 为新的后端类型
2. 可选: 提供必要的后端特定配置
3. 重启应用或重新初始化 `MemoryService`

---

遵循本文档中的开发标准，您可以开发兼容而可替换的 Memory 后端插件，并确保它们可以无缝集成到 VibeCopilot 的知识库系统中。对于用户而言，切换后端将是透明的，不需要修改使用 `MemoryService` 的代码。
