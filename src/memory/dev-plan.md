# 记忆管理系统

## 当前状态

记忆管理系统实现了基本功能，可通过命令行接口与Basic Memory集成。目前支持：

1. **笔记管理**：创建、读取、更新、删除笔记
2. **内容查询**：列出、搜索知识库内容
3. **索引清理**：删除操作已优化，确保同时清理物理文件和搜索索引
4. **服务层抽象**：实现了模块化的服务层设计，隔离命令层和具体实现
5. **本地索引**：使用MemoryItem作为本地索引，加速检索和维护数据一致性
6. **工具辅助**：使用路径处理、文本处理和时间处理工具函数，提升代码质量

## 系统架构

记忆管理系统使用三层架构：

1. **命令层**：处理CLI命令参数和调用逻辑
2. **服务层**：实现核心业务逻辑，封装底层实现细节
3. **存储层**：通过Basic Memory实现实际存储功能

### 服务层模块

- `NoteService`：处理笔记的CRUD操作
- `SearchService`：提供列表和搜索功能
- `SyncService`：处理本地内容与知识库的同步
- `MemoryItemService`：管理本地数据库中的记忆项并与Basic Memory同步

## 数据同步机制

### Basic Memory与MemoryItem的同步

系统维护了两层存储：

1. **Basic Memory**：负责实际内容存储，提供语义搜索能力
2. **MemoryItem**：本地SQLite数据库，存储元数据和同步状态

同步机制如下：

- **创建内容时**：
  1. 首先在Basic Memory中创建内容
  2. 获取永久链接(permalink)
  3. 在MemoryItem中创建记录，存储永久链接和元数据

- **更新内容时**：
  1. 更新Basic Memory中的内容
  2. 更新MemoryItem中的同步状态和元数据

- **删除内容时**：
  1. 在Basic Memory中删除内容和索引
  2. 在MemoryItem中标记为已删除

- **定期同步**：
  1. 从Basic Memory获取最新内容列表
  2. 与MemoryItem进行比对
  3. 双向同步变更内容
  4. 更新同步状态

### 查询流程优化

查询时利用两层存储特点：

1. **快速查询**：首先查询MemoryItem数据库获取元数据和永久链接
2. **详细内容**：使用永久链接从Basic Memory获取完整内容
3. **缓存机制**：频繁访问的内容可在MemoryItem中缓存

这种设计提供了以下优势：

- 显著提高查询速度（本地SQL查询比Basic Memory API调用快）
- 减少网络请求和外部依赖
- 支持离线操作和批量同步
- 维护一致的同步状态跟踪

## 已知问题

- 对文件路径/标识符处理存在复杂性，需要处理多种变体
- 在同步过程中可能出现冲突，需要更好的冲突解决策略

## 后续开发计划

1. **完善服务层**：
   - 完成剩余功能迁移到服务层
   - 添加单元测试
   - 优化配置管理

2. **同步机制增强**：
   - 实现增量同步策略
   - 添加冲突检测和解决机制
   - 优化大规模数据同步性能

3. **实体管理系统**：
   - 实现`entity_manager.py`核心功能
   - 添加实体类型定义和属性验证
   - 开发实体关系图可视化

4. **观察管理系统**：
   - 实现`observation_manager.py`
   - 开发观察记录和检索功能
   - 添加时间线视图

5. **关系管理系统**：
   - 实现`relation_manager.py`
   - 开发关系类型定义
   - 实现关系查询和路径分析

## 优先任务

1. 完善MemoryItem与Basic Memory的同步策略
2. 优化路径处理逻辑，减少变体处理复杂性
3. 增加单元测试覆盖率
4. 添加批量操作支持

## 技术债务

1. 路径处理逻辑已重构，但需要进一步完善
2. 错误处理需统一化
3. 索引管理需更严格的一致性保证

## 服务层使用示例

### 笔记服务

```python
from src.memory import NoteService

# 创建服务实例
note_service = NoteService()

# 创建笔记
success, message, result = note_service.create_note(
    content="这是笔记内容",
    title="示例笔记",
    folder="notes"
)

# 读取笔记
success, content, metadata = note_service.read_note("notes/示例笔记")

# 更新笔记
success, message, result = note_service.update_note(
    path="notes/示例笔记",
    content="这是更新后的内容"
)

# 删除笔记
success, message, result = note_service.delete_note("notes/示例笔记")
```

### 搜索服务

```python
from src.memory import SearchService

# 创建服务实例
search_service = SearchService()

# 列出笔记
success, message, notes = search_service.list_notes()

# 搜索笔记
success, message, results = search_service.search_notes("搜索关键词")
```

### 同步服务

```python
from src.memory import SyncService

# 创建服务实例
sync_service = SyncService()

# 同步所有内容
success, message, result = sync_service.sync_all()

# 同步规则
success, message, result = sync_service.sync_rules()

# 同步文档
success, message, result = sync_service.sync_documents()

# 导入外部文档
success, message, result = sync_service.import_documents("/path/to/docs")
```

### 记忆项服务

```python
from src.memory import MemoryItemService

# 创建服务实例
item_service = MemoryItemService()

# 创建记忆项
item = item_service.create_item(
    title="示例记忆项",
    content="这是记忆项内容",
    folder="examples",
    tags="示例,测试"
)

# 使用永久链接获取记忆项
item = item_service.get_item_by_permalink("memory://examples/示例记忆项")

# 搜索记忆项
items = item_service.search_items(query="示例", folder="examples")

# 从Basic Memory同步
note_data = {"title": "远程笔记", "content": "内容", "permalink": "memory://notes/远程笔记"}
item, is_new = item_service.sync_from_remote(note_data)

# 获取数据库信息
db_info = item_service.get_db_info()
```

## 工具函数使用

### 路径处理工具

```python
from src.memory.helpers import (
    normalize_path, join_paths, ensure_dir_exists,
    path_to_permalink, permalink_to_path, is_permalink
)

# 规范化路径
path = normalize_path("folder/subfolder/../file.md")  # "folder/file.md"

# 连接路径
full_path = join_paths("base", "folder", "file.md")  # "base/folder/file.md"

# 确保目录存在
success = ensure_dir_exists("data/output", create=True)

# 转换为永久链接
permalink = path_to_permalink("/path/to/file.md")  # "memory://path/to/file.md"

# 从永久链接获取路径
path = permalink_to_path("memory://path/to/file.md")  # "/path/to/file.md"

# 检查是否为永久链接
is_plink = is_permalink("memory://path/to/file.md")  # True
```

### 文本处理工具

```python
from src.memory.helpers import (
    clean_text, normalize_text, extract_plain_text,
    calculate_text_similarity, highlight_text
)

# 清理文本
clean = clean_text("  多余  空格和\t制表符  ")  # "多余 空格和 制表符"

# 规范化文本
norm = normalize_text("TEXT with Punctuation!", lowercase=True)  # "text with punctuation!"

# 提取纯文本
plain = extract_plain_text("# Markdown 标题\n[链接](https://example.com)")  # "Markdown 标题 链接"

# 计算相似度
similarity = calculate_text_similarity("hello world", "hello earth")  # 0.6

# 高亮显示
highlights = highlight_text("这是一段长文本，包含关键词", "关键词")  # ["...包含关键词"]
```

## 参考资源

- Basic Memory CLI文档
- Vector Database最佳实践
- 实体-关系模型设计指南
- SQLite性能优化指南
