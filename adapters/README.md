# VibeCopilot 适配器模块

适配器模块提供了一系列灵活的接口和工具，用于连接 VibeCopilot 核心功能与外部系统、服务和数据格式。该模块充当中间层，简化集成并标准化数据交换。

## 模块结构

```
adapters/
├── content_parser/     # 内容解析适配器 (OpenAI, Ollama)
├── docs_engine.py      # 文档引擎统一接口
├── docusaurus/         # Docusaurus文档网站适配器
├── obsidian/           # Obsidian知识库适配器
└── rule_parser/        # 规则解析适配器
```

## 模块分类

### 内容解析 (content_parser)

提供通用接口，使用LLM解析各种格式的内容：

- 自动检测并使用适当的解析器（OpenAI、Ollama等）
- 支持规则、Markdown文档、代码等多种内容类型
- 统一输出格式，简化下游处理

```python
from adapters.content_parser import parse_file, parse_content

# 解析文件
result = parse_file("path/to/file.md", content_type="document")

# 解析内容
result = parse_content("# 标题\n内容", content_type="document")
```

### 文档引擎 (docs_engine)

提供文档处理、转换和管理功能：

- 使用内容解析器解析文档结构
- 提供文档块提取和管理
- 支持文档导入到数据库

```python
from adapters.docs_engine import parse_document_file, import_document_to_db

# 解析文档
doc_data = parse_document_file("path/to/document.md")

# 导入到数据库
result = import_document_to_db("path/to/document.md")
```

### 外部系统集成

#### Obsidian 适配器

与 Obsidian 知识库交互：

- 监控文件变更
- 语法检查
- 同步功能

```python
from adapters.obsidian import FileWatcher

# 监控文件变更
watcher = FileWatcher("/path/to/vault", callback_function)
watcher.start()
```

#### Docusaurus 适配器

与 Docusaurus 文档网站交互：

- 文档同步
- 索引生成
- 侧边栏配置生成

```python
from adapters.docusaurus import DocusaurusSync, IndexGenerator

# 同步文档
sync = DocusaurusSync("/source/path", "/docusaurus/path")
sync.sync_all()

# 生成索引
generator = IndexGenerator("/docusaurus/path")
generator.generate_all_indices()
```

## 命令行工具

各适配器模块提供独立的命令行工具：

- **docs_engine CLI**: 文档解析、转换和管理
  ```bash
  python -m src.docs_engine.cli parse document.md --output result.json
  ```

- **Obsidian CLI**: 知识库监控和检查
  ```bash
  python -m adapters.obsidian.cli --vault /path/to/vault watch
  ```

- **Docusaurus CLI**: 文档同步和索引生成
  ```bash
  python -m adapters.docusaurus.cli --source /source --target /target sync
  ```

## 配置

适配器模块通常通过环境变量或配置文件进行配置：

```bash
# 内容解析器配置
export OPENAI_API_KEY="your-api-key"
export CONTENT_PARSER_TYPE="openai"  # 或 "ollama"

# 文档引擎配置
export TEMPLATES_DIR="/path/to/templates"
```

配置详情请参阅各子模块的 README 文件。

## 设计原则

- **接口统一**: 提供一致的接口，隐藏底层实现细节
- **可扩展性**: 易于添加新的适配器或解析器
- **关注点分离**: 每个适配器专注于特定的集成需求
- **容错性**: 适当的错误处理和降级机制
- **可测试性**: 清晰的接口便于单元测试
