# VibeCopilot 配置说明

本目录包含VibeCopilot项目的配置文件和示例。

## 环境变量

VibeCopilot使用环境变量进行配置，主要环境变量文件为项目根目录下的`.env`文件。
`.env.example`为示例配置文件，可以复制为`.env`并根据需要修改。

### 核心配置

- `APP_NAME`: 应用名称
- `APP_ENV`: 应用环境，可选值为`development`, `testing`, `production`
- `DEBUG`: 是否启用调试模式
- `LOG_LEVEL`: 日志级别，可选值为`debug`, `info`, `warning`, `error`, `critical`

### AI集成配置

- `OPENAI_API_KEY`: OpenAI API密钥
- `AI_MODEL`: 默认使用的AI模型
- `PROVIDER`: AI服务提供商，可选值为`openai`, `anthropic`等

### 规则解析配置

规则解析系统用于将Markdown格式的规则文件解析为结构化数据，支持以下配置：

- `VIBE_RULE_PARSER`: 规则解析使用的引擎，可选值为：
  - `openai`: 使用OpenAI API进行解析（默认，需要API密钥）
  - `ollama`: 使用本地Ollama服务进行解析（免费，需要安装Ollama）

- `VIBE_OPENAI_MODEL`: 使用OpenAI解析规则时的模型，默认为`gpt-4o-mini`
- `VIBE_OLLAMA_MODEL`: 使用Ollama解析规则时的模型，默认为`llama3`
- `VIBE_OLLAMA_BASE_URL`: Ollama服务地址，默认为`http://localhost:11434`

注意：

- 如果选择`openai`解析器，必须设置有效的`OPENAI_API_KEY`
- 如果选择`ollama`解析器，必须确保Ollama服务已启动并可访问

### 项目设置

- `PROJECT_DIR`: 项目目录
- `DEFAULT_TEMPLATE`: 默认模板
- `AUTO_SAVE`: 是否自动保存
- `AUTO_BACKUP`: 是否自动备份

### GitHub集成

- `GITHUB_TOKEN`: GitHub个人访问令牌
- `GITHUB_OWNER`: GitHub仓库拥有者
- `GITHUB_REPO`: GitHub仓库名称

### 路线图配置

- `ROADMAP_PROJECT_NAME`: 路线图项目标题

### Obsidian同步

- `DOCS_SOURCE_DIR`: 标准Markdown文档源目录
- `OBSIDIAN_VAULT_DIR`: Obsidian知识库目录
- `AUTO_SYNC_DOCS`: 是否自动同步文档到Obsidian
- `AUTO_SYNC_INTERVAL`: 自动同步间隔(秒)
