# VibeCopilot环境配置工具

本目录包含VibeCopilot项目的环境配置工具脚本。

## 主要功能

`init_project.py`专注于以下功能：

1. 自动设置Python开发环境
2. 安装项目依赖
3. 注册命令行工具
4. 配置Node.js开发环境
5. 安装并配置pnpm及markdownlint
6. 创建必要的配置文件符号链接
7. 检查和配置MCP服务器环境

## 使用方法

```bash
# 在VibeCopilot项目根目录运行
python scripts/setup/init_project.py
```

## 技术细节

### 模块化结构

- 采用模块化设计，提高代码可维护性
- 各功能模块位于`modules/`目录下
- Node.js相关功能拆分为多个专用模块：
  - `node/version.py` - Node.js版本和工具管理
  - `node/dependencies.py` - 依赖检查和安装
  - `node/mcp.py` - MCP服务器配置
  - `node/setup.py` - 整合模块的主设置流程

### Python环境

- 使用Python 3.13作为默认Python环境
- 使用uv作为包管理工具
- 自动创建虚拟环境(.venv)
- 安装项目依赖(包括dev和docs可选依赖)
- 注册vibecopilot命令行工具

### Node.js环境

- 检查并使用Node.js环境
- 支持nvm进行版本管理（多平台兼容）
- 使用pnpm作为包管理器（优先于npm）
- 配置monorepo工作区结构
- 安装markdownlint-cli等开发工具
- 自动配置PATH环境变量
- 智能依赖版本检查，避免冲突

### MCP服务器配置

- 自动检查npx和uvx工具可用性
- 检查现有.cursor/mcp.json配置文件并提供建议
- MCP服务器为临时执行工具，包括：
  - filesystem - 文件系统操作
  - sequential-thinking - 顺序思考
  - time - 时间处理
  - basic-memory - 基本内存
  - git - Git操作
- 特别注意：MCP服务器不支持安装到项目依赖，只能通过npx/uvx临时执行

### 开发工具配置

- 配置pre-commit钩子
- 设置markdownlint检查
- 配置文档链接检查器

### 配置文件管理

- 配置文件存放在`config/default`目录
- 为pre-commit创建必要的符号链接
- 自动清理冗余的配置文件

## 依赖

- Python 3.13+ (`brew install python@3.13`)
- Node.js (`brew install node`或通过nvm安装)
- uv (自动安装)
- pnpm (自动安装)
- npm (用于npx临时执行)
- uvx (可选，用于部分MCP服务器)

## 跨平台支持

- 支持macOS、Linux和Windows操作系统
- 为不同平台提供适当的安装指令
- 自动处理路径和环境变量差异

## IDE设置建议

为了获得最佳的规则编辑体验，我们强烈建议更新您的Cursor设置：

```json
"workbench.editorAssociations": {
  "*.mdc": "default"
}
```

这一设置可以：

- 防止.mdc文件在自定义规则表单中出现UI渲染问题
- 确保正确的保存功能
- 使查看实际规则内容更容易（特别是查看隐藏的FrontMatter部分）

您可以在Cursor设置中手动添加此配置，或使用设置UI界面进行添加。

## 安装后

安装完成后，您可以：

1. 激活虚拟环境：

```bash
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

2. 使用命令行工具：

```bash
vibecopilot --help  # 查看帮助
```

3. 使用pnpm管理Node.js依赖：

```bash
pnpm add <package>      # 添加依赖
pnpm run <script>       # 运行脚本
pnpm exec markdownlint  # 运行markdownlint
```

4. 使用MCP服务器：

```bash
# 使用npx运行服务器
npx -y @modelcontextprotocol/server-filesystem ~/project

# 使用uvx运行服务器
uvx mcp-server-time --local-timezone Asia/Shanghai
uvx basic-memory mcp --project VibeCopilot
```

5. 退出虚拟环境：

```bash
deactivate
```
