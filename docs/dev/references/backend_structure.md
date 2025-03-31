# VibeCopilot 后端结构

本文档详细说明VibeCopilot后端的架构设计、API设计、数据模型、目录结构以及开发规范。

## 1. 架构概览

VibeCopilot采用模块化、松耦合的后端架构，主要基于Python实现。

### 1.1 核心架构原则

- **模块化设计**: 将功能按职责分离为独立模块
- **依赖注入**: 通过依赖注入实现模块间松耦合
- **领域驱动设计**: 关注核心业务领域和逻辑
- **统一接口**: 使用一致的API设计风格
- **可扩展性**: 支持通过插件扩展功能

### 1.2 架构层次

```
┌─────────────────────────────────────────────────────┐
│                    接口层 (Interfaces)               │
│  CLI, MCP工具接口, FastAPI HTTP接口, WebSocket接口   │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                  应用层 (Application)                │
│              服务协调, 流程控制, 事件处理            │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                   领域层 (Domain)                    │
│             核心业务逻辑, 领域模型, 规则             │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│                  基础设施层 (Infrastructure)         │
│         数据持久化, 外部服务集成, 工具和助手         │
└─────────────────────────────────────────────────────┘
```

### 1.3 主要组件

- **核心引擎 (Core Engine)**: 协调各模块，管理项目状态和流程
- **文档管理器 (Document Manager)**: 处理文档模板、生成和版本控制
- **AI集成服务 (AI Integration)**: 与AI提供商集成，管理提示词和上下文
- **项目分析器 (Project Analyzer)**: 分析项目代码和结构
- **工具推荐服务 (Tools Recommendation)**: 根据上下文推荐合适的工具
- **状态管理器 (State Manager)**: 处理项目状态追踪和进度报告
- **配置服务 (Config Service)**: 管理用户和应用配置

## 2. API设计

### 2.1 API风格

VibeCopilot采用REST API设计，遵循以下原则：

- 使用标准HTTP方法 (GET, POST, PUT, DELETE)
- 资源路径使用名词复数 (/projects, /documents)
- 版本控制通过URL路径 (/api/v1/...)
- 查询参数用于过滤、排序和分页
- 使用HTTP状态码表示结果状态
- 统一的响应格式

### 2.2 主要API端点

#### 项目管理API

```
GET    /api/v1/projects                 # 获取项目列表
POST   /api/v1/projects                 # 创建新项目
GET    /api/v1/projects/{id}            # 获取项目详情
PUT    /api/v1/projects/{id}            # 更新项目
DELETE /api/v1/projects/{id}            # 删除项目
GET    /api/v1/projects/{id}/status     # 获取项目状态
POST   /api/v1/projects/{id}/advance    # 推进项目阶段
```

#### 文档管理API

```
GET    /api/v1/projects/{id}/documents           # 获取项目文档列表
POST   /api/v1/projects/{id}/documents           # 创建新文档
GET    /api/v1/projects/{id}/documents/{doc_id}  # 获取文档内容
PUT    /api/v1/projects/{id}/documents/{doc_id}  # 更新文档
DELETE /api/v1/projects/{id}/documents/{doc_id}  # 删除文档
PATCH  /api/v1/projects/{id}/documents/{doc_id}/status # 更新文档状态
```

#### 任务管理API

```
GET    /api/v1/projects/{id}/phases/{phase}/tasks  # 获取阶段任务
POST   /api/v1/projects/{id}/phases/{phase}/tasks  # 创建任务
PUT    /api/v1/projects/{id}/phases/{phase}/tasks/{task_id} # 更新任务
```

#### AI集成API

```
POST   /api/v1/ai/code-assist        # 代码辅助
POST   /api/v1/ai/doc-assist         # 文档辅助
POST   /api/v1/ai/prompts            # 创建提示词
GET    /api/v1/ai/prompts            # 获取提示词列表
GET    /api/v1/ai/prompts/{id}       # 获取提示词
```

#### 工具推荐API

```
GET    /api/v1/tools                   # 获取工具列表
POST   /api/v1/tools/recommend         # 获取工具推荐
GET    /api/v1/tools/categories        # 获取工具类别
```

### 2.3 API响应格式

成功响应:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 10,
    "total": 42
  }
}
```

错误响应:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { ... }
  }
}
```

### 2.4 API认证与安全

- 使用API密钥或JWT令牌进行认证
- 实现请求限流防止滥用
- 跨域资源共享(CORS)设置
- 输入验证防止注入攻击

## 3. 数据模型

### 3.1 核心数据模型

#### Project (项目)

```python
class Project:
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    current_phase: str
    overall_progress: int
    settings: Dict[str, Any]
```

#### Phase (阶段)

```python
class Phase:
    id: str
    project_id: str
    name: str
    status: str  # not_started, in_progress, completed, etc.
    progress: int
    order: int
    tasks: List[Task]
```

#### Task (任务)

```python
class Task:
    id: str
    phase_id: str
    description: str
    status: str  # not_started, in_progress, completed, blocked, etc.
    progress: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
```

#### Document (文档)

```python
class Document:
    id: str
    project_id: str
    type: str  # prd, tech_stack, etc.
    title: str
    content: str
    status: str  # not_created, in_progress, created
    created_at: datetime
    updated_at: datetime
    version: int
    metadata: Dict[str, Any]
```

#### PromptTemplate (提示词模板)

```python
class PromptTemplate:
    id: str
    name: str
    description: str
    template: str
    variables: List[str]
    task_type: str  # code_generation, documentation, etc.
    model: str  # gpt-4, claude-3, etc.
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
```

#### Tool (工具)

```python
class Tool:
    id: str
    name: str
    description: str
    url: str
    categories: List[str]
    language_support: List[str]
    platform: List[str]
    install_command: str
    documentation_url: str
    popularity: int
    metadata: Dict[str, Any]
```

### 3.2 数据存储策略

VibeCopilot采用混合存储策略:

1. **SQLite** - 本地轻量级数据存储
   - 项目元数据
   - 状态信息
   - 配置数据

2. **文件系统** - 文档和内容存储
   - 文档内容 (Markdown)
   - 配置文件 (YAML/JSON)
   - 模板文件

3. **可选云存储** - 备份和协作
   - 项目备份
   - 团队协作
   - 共享模板

## 4. 模块划分

VibeCopilot后端被划分为以下主要模块，每个模块具有明确的职责和边界:

### 4.1 核心模块

#### 4.1.1 Core Engine (核心引擎)

负责整个系统的协调和控制流程。

**主要职责**:
- 协调各模块之间的交互
- 处理主要业务逻辑
- 维护系统状态
- 处理事件分发
- 提供全局服务注册和发现

**核心类**:
- `Engine`: 中央协调器
- `ServiceRegistry`: 服务注册表
- `EventBus`: 事件总线
- `WorkflowManager`: 工作流管理器

#### 4.1.2 State Manager (状态管理器)

管理项目状态和进度跟踪。

**主要职责**:
- 追踪项目整体状态
- 管理项目阶段和任务状态
- 计算完成度和进度
- 提供状态变更通知
- 管理状态持久化

**核心类**:
- `StateManager`: 状态管理主类
- `ProjectState`: 项目状态模型
- `PhaseTracker`: 阶段跟踪器
- `TaskTracker`: 任务跟踪器
- `ProgressCalculator`: 进度计算器

### 4.2 功能模块

#### 4.2.1 Document Manager (文档管理器)

处理项目文档的生成、管理和版本控制。

**主要职责**:
- 管理文档模板
- 生成项目文档
- 处理文档版本控制
- 提供文档内容解析和渲染
- 管理文档元数据

**核心类**:
- `DocumentManager`: 文档管理主类
- `TemplateEngine`: 模板引擎
- `MarkdownRenderer`: Markdown渲染器
- `DocumentStore`: 文档存储
- `VersionController`: 版本控制器

#### 4.2.2 AI Integration (AI集成)

集成各种AI服务，处理提示词管理和上下文处理。

**主要职责**:
- 集成多种AI模型提供商
- 管理提示词模板
- 处理上下文构建
- 优化AI请求参数
- 处理AI响应解析

**核心类**:
- `AIManager`: AI管理主类
- `PromptManager`: 提示词管理器
- `ContextBuilder`: 上下文构建器
- `ModelSelector`: 模型选择器
- `ResponseParser`: 响应解析器

#### 4.2.3 Project Analyzer (项目分析器)

分析项目代码和结构，提供分析结果。

**主要职责**:
- 分析项目代码结构
- 提取项目依赖
- 识别编程语言和框架
- 分析代码复杂度
- 生成项目报告

**核心类**:
- `ProjectAnalyzer`: 项目分析主类
- `CodeParser`: 代码解析器
- `DependencyAnalyzer`: 依赖分析器
- `StructureExtractor`: 结构提取器
- `AnalysisReporter`: 分析报告生成器

#### 4.2.4 Tools Recommendation (工具推荐)

基于项目上下文推荐合适的开发工具。

**主要职责**:
- 维护工具数据库
- 基于上下文推荐工具
- 提供工具搜索功能
- 跟踪工具使用情况
- 更新工具元数据

**核心类**:
- `ToolsManager`: 工具管理主类
- `RecommendationEngine`: 推荐引擎
- `ToolsDatabase`: 工具数据库
- `ContextMatcher`: 上下文匹配器
- `UsageTracker`: 使用情况跟踪器

### 4.3 基础设施模块

#### 4.3.1 Config Service (配置服务)

管理系统和用户配置。

**主要职责**:
- 加载和保存配置
- 提供默认配置
- 验证配置有效性
- 处理配置变更
- 提供配置访问接口

**核心类**:
- `ConfigManager`: 配置管理主类
- `ConfigStore`: 配置存储
- `ConfigValidator`: 配置验证器
- `UserPreferences`: 用户偏好
- `DefaultsProvider`: 默认配置提供者

#### 4.3.2 Data Storage (数据存储)

处理数据持久化和存储。

**主要职责**:
- 提供数据访问接口
- 管理数据迁移
- 处理数据备份
- 实现数据缓存
- 管理存储引擎连接

**核心类**:
- `StorageManager`: 存储管理主类
- `DatabaseConnector`: 数据库连接器
- `FileSystemStore`: 文件系统存储
- `Migrator`: 数据迁移器
- `BackupManager`: 备份管理器

## 5. 目录结构

VibeCopilot后端采用功能模块化的目录结构，清晰地分离不同的功能组件：

```
vibecopilot/
├── __init__.py                # 包初始化
├── main.py                    # 主入口点
├── config.py                  # 全局配置
├── core/                      # 核心引擎
│   ├── __init__.py
│   ├── engine.py              # 核心引擎实现
│   ├── service_registry.py    # 服务注册表
│   ├── event_bus.py           # 事件总线
│   └── workflow.py            # 工作流管理
│
├── state/                     # 状态管理
│   ├── __init__.py
│   ├── state_manager.py       # 状态管理器
│   ├── project_state.py       # 项目状态
│   ├── phase.py               # 阶段管理
│   └── task.py                # 任务管理
│
├── document/                  # 文档管理
│   ├── __init__.py
│   ├── document_manager.py    # 文档管理器
│   ├── template_engine.py     # 模板引擎
│   ├── renderer.py            # 渲染器
│   └── version_control.py     # 版本控制
│
├── ai/                        # AI集成
│   ├── __init__.py
│   ├── ai_manager.py          # AI管理器
│   ├── prompt_manager.py      # 提示词管理
│   ├── context_builder.py     # 上下文构建
│   └── model_connector.py     # 模型连接器
│
├── analyzer/                  # 项目分析
│   ├── __init__.py
│   ├── project_analyzer.py    # 项目分析器
│   ├── code_parser.py         # 代码解析
│   ├── dependency_analyzer.py # 依赖分析
│   └── report_generator.py    # 报告生成
│
├── tools/                     # 工具推荐
│   ├── __init__.py
│   ├── tools_manager.py       # 工具管理器
│   ├── recommendation.py      # 推荐引擎
│   ├── tools_database.py      # 工具数据库
│   └── usage_tracker.py       # 使用情况跟踪
│
├── config/                    # 配置服务
│   ├── __init__.py
│   ├── config_manager.py      # 配置管理器
│   ├── user_preferences.py    # 用户偏好
│   └── defaults.py            # 默认配置
│
├── storage/                   # 数据存储
│   ├── __init__.py
│   ├── storage_manager.py     # 存储管理器
│   ├── database.py            # 数据库连接
│   ├── file_system.py         # 文件系统存储
│   └── migrations/            # 数据迁移
│
├── api/                       # API接口
│   ├── __init__.py
│   ├── app.py                 # FastAPI应用
│   ├── routes/                # API路由
│   │   ├── __init__.py
│   │   ├── projects.py        # 项目相关路由
│   │   ├── documents.py       # 文档相关路由
│   │   ├── ai.py              # AI相关路由
│   │   └── tools.py           # 工具相关路由
│   ├── models/                # API数据模型
│   └── middleware/            # API中间件
│
├── cli/                       # 命令行接口
│   ├── __init__.py
│   ├── app.py                 # CLI主应用
│   ├── commands/              # CLI命令
│   │   ├── __init__.py
│   │   ├── init.py            # 初始化命令
│   │   ├── status.py          # 状态命令
│   │   └── update.py          # 更新命令
│   └── formatters/            # 输出格式化
│
├── mcp/                       # MCP工具接口
│   ├── __init__.py
│   ├── connector.py           # MCP连接器
│   └── handlers.py            # MCP处理器
│
├── templates/                 # 文档模板
│   ├── project/               # 项目模板
│   ├── docs/                  # 文档模板
│   └── code/                  # 代码模板
│
├── utils/                     # 工具函数
│   ├── __init__.py
│   ├── logger.py              # 日志工具
│   ├── exceptions.py          # 异常定义
│   └── helpers.py             # 辅助函数
│
└── tests/                     # 测试
    ├── __init__.py
    ├── conftest.py            # 测试配置
    ├── unit/                  # 单元测试
    ├── integration/           # 集成测试
    └── fixtures/              # 测试数据
```

## 6. 开发规范

### 6.1 编码规范

- 遵循PEP 8编码风格
- 使用类型注解提高代码可维护性
- 使用一致的命名约定
  - 类名: PascalCase
  - 变量/函数: snake_case
  - 常量: UPPER_SNAKE_CASE
  - 私有成员: _leading_underscore
- 编写清晰的文档字符串
- 限制函数复杂度，遵循单一职责原则

### 6.2 依赖管理

- 使用virtualenv或conda进行环境隔离
- 使用pyproject.toml定义项目元数据和依赖
- 明确指定依赖版本
- 区分开发依赖和运行时依赖
- 定期更新依赖并检查安全漏洞

### 6.3 测试策略

- 单元测试: 使用pytest框架
- 集成测试: 验证模块间协作
- 测试覆盖率目标: >80%
- 使用mock对象隔离外部依赖
- 实现持续集成测试

### 6.4 日志和错误处理

- 使用结构化日志记录
- 定义清晰的异常层次结构
- 在适当级别记录错误和警告
- 避免在生产环境中暴露敏感信息
- 实现优雅的错误恢复机制

### 6.5 安全最佳实践

- 不要硬编码敏感信息
- 使用安全的默认配置
- 输入验证和净化
- 正确处理用户认证和授权
- 遵循最小权限原则

### 6.6 性能考虑

- 适当使用缓存
- 异步处理长时间运行的任务
- 避免不必要的I/O操作
- 优化数据库查询
- 批量处理大量数据

### 6.7 协作规范

- 使用Git进行版本控制
- 采用基于功能分支的工作流
- 提交前进行代码检查
- 代码审查所有更改
- 编写清晰的提交消息
