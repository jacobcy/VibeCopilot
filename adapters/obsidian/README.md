# Obsidian 适配器

此模块提供与 Obsidian 知识库交互的功能，包括文件监控、同步和格式转换。

## 主要功能

- 监控 Obsidian 知识库的文件变更
- 将 Obsidian 文档转换为标准格式
- 同步 Obsidian 文档到其他系统

## 组件

### 文件监控器 (File Watcher)

`FileWatcher` 类负责监控 Obsidian 知识库中的文件变更，并在文件被创建、修改或删除时触发回调函数。

```python
from adapters.obsidian import FileWatcher

# 创建文件监控器
watcher = FileWatcher("/path/to/obsidian/vault", callback_function)

# 开始监控
watcher.start()

# 停止监控
watcher.stop()
```

### 语法检查器 (Syntax Checker)

`SyntaxChecker` 类提供检查 Obsidian 特有语法的功能，确保文档语法正确。

```python
from adapters.obsidian.syntax_checker import check_syntax

# 检查文档语法
issues = check_syntax(content)
```

## 配置选项

Obsidian 适配器使用以下环境变量进行配置：

- `OBSIDIAN_VAULT_DIR` - Obsidian 知识库目录
- `AUTO_SYNC_DOCS` - 是否自动同步文档
- `AUTO_SYNC_INTERVAL` - 自动同步间隔(秒)

## 与其他模块的集成

Obsidian 适配器与以下模块集成：

- `src/parsing` - 用于解析 Obsidian 文档
- `docs_engine` - 使用文档引擎进行格式转换
- `docusaurus` - 同步文档到 Docusaurus
