# VibeCopilot 文档引擎

文档引擎是VibeCopilot的核心模块之一，提供Obsidian与Docusaurus之间的文档转换与同步功能。

## 核心功能

- **链接转换**：在Obsidian双向链接和Docusaurus标准Markdown链接之间转换
- **目录生成**：自动创建分类目录索引
- **模板管理**：提供标准化的文档模板
- **实时同步**：监控文档变更并实时同步
- **配置管理**：统一管理Obsidian和Docusaurus配置

## 快速开始

### 基本使用

```python
from src.docs_engine.docs_engine import create_docs_engine

# 创建文档引擎实例
docs_engine = create_docs_engine('/path/to/project/root')

# 全量同步文档
stats = docs_engine.sync_all()
print(f"同步完成: 添加 {stats['added']}，更新 {stats['updated']}，删除 {stats['deleted']}")

# 使用模板创建新文档
docs_engine.generate_new_document(
    template='default',
    output_path='/path/to/project/root/docs/new-document.md',
    variables={
        'title': '新文档',
        'description': '这是一个示例文档',
        'category': '示例'
    }
)

# 停止文档引擎（停止文件监控等）
docs_engine.stop()
```

### 高级功能

#### 验证文档链接

```python
# 验证所有文档链接
broken_links = docs_engine.validate_links()
for file_path, links in broken_links.items():
    print(f"文件: {file_path}")
    for link in links:
        print(f"  无效链接: {link['text']} ({link['target']})")
```

#### 生成Docusaurus侧边栏

```python
# 生成侧边栏配置
sidebar_config = docs_engine.generate_docusaurus_sidebar()

# 写入配置文件
import json
with open('/path/to/project/root/website/sidebars.json', 'w', encoding='utf-8') as f:
    json.dump(sidebar_config, f, indent=2)
```

## 模块结构

```
docs_engine/
├── __init__.py           # 模块初始化
├── docs_engine.py        # 主模块，整合所有功能
├── config/               # 配置管理
│   ├── __init__.py
│   └── config_manager.py # 配置管理器
├── converters/           # 格式转换
│   ├── __init__.py
│   ├── link_converter.py # 链接转换
│   └── index_generator.py# 索引生成
├── sync/                 # 同步工具
│   ├── __init__.py
│   ├── docusaurus_sync.py# Docusaurus同步
│   └── file_watcher.py   # 文件监控
└── templates/            # 文档模板
    ├── __init__.py
    └── template_manager.py # 模板管理
```

## 配置选项

文档引擎的配置存储在`config/docs_config.json`文件中，包含以下主要部分：

- **obsidian**: Obsidian相关配置
  - `vault_dir`: Obsidian文档库目录
  - `exclude_patterns`: 要排除的文件模式
  - `plugins`: 需要配置的插件列表

- **docusaurus**: Docusaurus相关配置
  - `content_dir`: Docusaurus文档目录
  - `sidebar_category_order`: 侧边栏分类顺序

- **sync**: 同步相关配置
  - `auto_sync`: 是否自动同步
  - `watch_for_changes`: 是否监控文件变更
  - `sync_on_startup`: 启动时是否同步
  - `backup_before_sync`: 同步前是否备份

- **templates**: 模板相关配置
  - `template_dir`: 模板目录
  - `default_template`: 默认模板
  - `default_category`: 默认分类

## 依赖项

- Python 3.7+
- PyYAML: 用于处理YAML前置元数据
- watchdog: 用于文件监控
