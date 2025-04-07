# Basic Memory

Basic Memory 是一个工具集，专为知识管理和信息提取而设计。通过解析各种文本内容，提取实体关系，并支持将这些结构化信息导出到不同格式。

## 功能特点

- **文档解析**：支持多种解析器（OpenAI、Ollama、正则表达式）
- **实体关系提取**：从文档中自动提取实体、关系和观察
- **导出功能**：支持导出到Obsidian等格式
- **命令行工具**：提供易用的CLI界面

## 使用方法

### 安装

```bash
# 为CLI工具创建符号链接
ln -sf $(pwd)/scripts/basicmem /usr/local/bin/basicmem
ln -sf $(pwd)/scripts/bm /usr/local/bin/bm
```

### 命令行工具

```bash
# 显示帮助
basicmem --help

# 解析单个文件
basicmem parse example.md --parser regex

# 解析整个目录
basicmem parse ./docs/ --recursive

# 批量导入文档到数据库
basicmem import ./documents/ --parser ollama --model mistral

# 导出到Obsidian格式
basicmem export ./output/data.json --format obsidian --output ./obsidian_vault
```

### 编程接口

```python
from adapters.basic_memory.parsers.regex_parser import RegexParser
from adapters.basic_memory.exporters.obsidian_exporter import ObsidianExporter
from adapters.basic_memory.db.memory_store import MemoryStore

# 解析文档
parser = RegexParser()
result = parser.parse_file("document.md")

# 存储到数据库
db = MemoryStore("/path/to/db.sqlite")
db.setup_database()
db.store_document(result, "document.md")

# 导出到Obsidian
exporter = ObsidianExporter("/path/to/obsidian_vault")
exporter.setup_output_dir()
exporter.export_all(db)
```

## 目录结构

```
adapters/basic_memory/
├── __init__.py          # 包初始化和版本信息
├── base.py              # 基础类定义
├── config.py            # 配置管理
├── cli/                 # 命令行接口
│   ├── __init__.py
│   ├── cli.py           # 主CLI入口
│   ├── parse_cmd.py     # 解析命令
│   ├── export_cmd.py    # 导出命令
│   └── import_cmd.py    # 导入命令
├── db/                  # 数据库操作
│   ├── __init__.py
│   └── memory_store.py  # 数据存储管理
├── parsers/             # 解析器实现
│   ├── __init__.py
│   └── regex_parser.py  # 正则表达式解析器
├── exporters/           # 导出器实现
│   ├── __init__.py
│   └── obsidian_exporter.py # Obsidian导出器
├── importer/            # 导入器实现（兼容旧版本）
└── utils/               # 工具函数
    ├── formatters.py    # 格式化工具
    └── file_utils.py    # 文件操作工具
```
