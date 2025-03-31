# VibeCopilot 技术栈

本文档详细说明VibeCopilot项目的技术选型决策，包括编程语言、框架、库和工具等。

## 1. 核心技术栈

### 编程语言

- **Python 3.10+**: 主要开发语言，具有强大的生态系统和易用性
- **TypeScript**: 用于前端界面和MCP插件开发

### 开发框架

- **FastAPI**: 用于API开发，性能优异，支持异步
- **React**: 用于开发简洁的Web界面组件
- **Electron**: (可选) 用于打包为桌面应用

### 数据存储

- **SQLite**: 本地数据存储，轻量级，无需额外安装
- **JSON/YAML文件**: 配置和模板存储
- **Git**: 版本控制和变更跟踪

## 2. 依赖库

### 后端

- **Pydantic**: 数据验证和设置管理
- **Jinja2**: 模板引擎，用于文档生成
- **PyGithub**: GitHub API集成
- **GitPython**: Git操作
- **LLama-Index/LangChain**: AI集成框架
- **Typer/Click**: 命令行界面
- **rich**: 终端美化和格式化输出

### 前端

- **shadcn/ui**: 组件库
- **TailwindCSS**: 样式系统
- **Zustand**: 状态管理
- **React Query**: 数据获取和缓存
- **Monaco Editor**: 代码编辑器组件

### 文档处理

- **markdown-it**: Markdown解析和渲染
- **mermaid-js**: 图表生成
- **remark/rehype**: Markdown处理工具链

## 3. 开发工具

### IDE和编辑器

- **Cursor/VSCode**: 主要开发环境
- **PyCharm**: (可选) Python开发

### 测试工具

- **pytest**: 单元测试和集成测试
- **React Testing Library**: 前端测试
- **Coverage.py**: 代码覆盖率分析

### 代码质量

- **Ruff**: 代码检查和格式化
- **ESLint/Prettier**: JavaScript/TypeScript代码检查和格式化
- **pre-commit**: Git提交前检查

### 构建和部署

- **Poetry**: Python依赖管理
- **Vite**: 前端构建工具
- **PyInstaller/cx_Freeze**: (可选) 打包为可执行文件

## 4. AI和NLP工具

- **OpenAI API**: 接入ChatGPT等大型语言模型
- **Cursor API**: 与Cursor编辑器集成
- **Hugging Face Transformers**: (可选) 本地模型支持
- **spaCy**: 自然语言处理任务

## 5. 集成服务

### 项目管理

- **GitHub/GitLab API**: 仓库管理和问题跟踪
- **Jira/Trello API**: 任务管理集成

### 文档和知识管理

- **Obsidian API**: 知识库集成
- **Notion API**: 文档集成

### CI/CD

- **GitHub Actions**: 自动化测试和部署
- **Docker**: 容器化(可选)

## 6. 技术决策理由

### Python作为主要语言

- 生态系统丰富，特别是在AI和自动化领域
- 开发效率高，适合快速迭代
- 跨平台支持良好

### FastAPI + React架构

- 分离后端逻辑和前端展示
- FastAPI提供高性能API，支持异步
- React生态系统成熟，组件丰富

### SQLite + 文件存储

- 无需额外数据库服务，降低使用门槛
- 适合轻量级数据存储需求
- 易于备份和版本控制

### OpenAI API集成

- 利用先进的大语言模型能力
- 无需本地训练和部署模型
- 可根据需要替换为其他模型API

## 7. 替代方案考虑

### Node.js + Express

- **优点**: JavaScript全栈，前后端语言统一
- **缺点**: Python在AI和自动化领域的库更丰富
- **决策**: 选择Python，但前端仍使用TypeScript/React

### 纯命令行工具

- **优点**: 简单，轻量，易于集成到工作流
- **缺点**: 用户体验有限，难以展示复杂信息
- **决策**: 主要提供MCP工具，同时保留命令行界面作为辅助

### MongoDB替代SQLite

- **优点**: 更灵活的文档存储
- **缺点**: 需要额外安装和配置，增加使用门槛
- **决策**: 选择SQLite以简化部署，后期可考虑增加MongoDB选项
