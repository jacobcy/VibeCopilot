# VibeCopilot

VibeCopilot是一个AI辅助开发工具，致力于优化开发流程，提高开发效率。当前处于演示阶段，专注于核心功能的实现。

## 主要功能

- **规则系统**：定义和管理开发规则和最佳实践
- **文档引擎**：管理、解析和检索项目文档
- **工作流管理**：规范化开发流程和任务管理
- **AI集成**：与OpenAI和Ollama等AI服务集成，增强开发能力

## 快速开始

1. 克隆项目

```bash
git clone https://github.com/jacobcy/VibeCopilot.git
cd VibeCopilot
```

2. 设置环境变量

```bash
cp config/.env.example .env
# 编辑.env文件，填入你的配置
```

3. 安装依赖

```bash
pip install -e .
```

4. 运行项目

```bash
vibecopilot --help
```

## 内容解析工具

VibeCopilot提供了统一的内容解析工具，支持解析规则文件和Markdown文档：

```bash
# 解析文件（自动检测内容类型）
content-parser parse path/to/file.md

# 解析规则文件
content-parser parse path/to/rule.mdc --type rule

# 解析文档文件
content-parser parse path/to/document.md --type document

# 解析文本内容
content-parser parse-content "# 文档标题\n\n文档内容" --type document

# 从文件读取内容并解析
content-parser parse-content path/to/file.md --from-file --type document

# 检查环境配置
content-parser check-env
```

## 项目结构

```
VibeCopilot/
├── adapters/              # 外部服务适配器
│   ├── content_parser/    # 统一内容解析模块
│   ├── rule_engine.py     # 规则引擎接口
│   └── docs_engine.py     # 文档引擎接口
├── src/                   # 核心源代码
│   ├── cli/               # 命令行接口
│   ├── core/              # 核心功能模块
│   ├── db/                # 数据库层
│   ├── docs_engine/       # 文档引擎
│   ├── models/            # 数据模型
│   └── workflow/          # 工作流管理
├── bin/                   # 可执行脚本
├── config/                # 配置文件
├── data/                  # 数据存储
├── docs/                  # 项目文档
└── tests/                 # 测试代码
```

## 环境变量

主要环境变量配置：

| 变量名 | 描述 | 默认值 |
|---------|-------------|---------|
| VIBE_CONTENT_PARSER | 内容解析引擎 | openai |
| VIBE_OPENAI_MODEL | OpenAI模型 | gpt-4o-mini |
| VIBE_OLLAMA_MODEL | Ollama模型 | mistral |
| OPENAI_API_KEY | OpenAI API密钥 | - |
| DOCS_ENGINE_DB_PATH | 文档引擎数据库路径 | data/docs_engine.db |

详细配置请参考`.env.example`文件。

## 许可证

MIT

## 贡献

欢迎提交问题和合并请求。

## LangChain解析器

VibeCopilot现在包含一个强大的LangChain解析器，支持文档知识化处理和基础内存功能。

### 主要功能

- 文档加载和分割
- 向量化存储与检索
- 知识实体和关系提取
- 知识图谱构建

### 使用方法

1. **基本用法**

   使用CLI命令导入文档:

   ```bash
   python -m adapters.basic_memory.cli import langchain ./docs
   ```

2. **高级选项**

   自定义数据库路径和模型:

   ```bash
   python -m adapters.basic_memory.cli import langchain ./docs \
     --db ./knowledge.db \
     --model gpt-4
   ```

3. **导出知识**

   将处理结果导出到Obsidian:

   ```bash
   python -m adapters.basic_memory.cli export ./knowledge.db --format obsidian
   ```

### 开发说明

LangChain解析器位于`adapters/basic_memory/parsers/langchain_parser.py`，它提供了一个简单的接口来处理文档并提取结构化知识。

要扩展功能，请完善以下模块:

- `document_loader.py`: 文档加载和分割
- `knowledge_extractor.py`: 知识提取
- `vector_store.py`: 向量存储管理
