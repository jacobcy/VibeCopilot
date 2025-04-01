# VibeCopilot 开发环境配置指南

本文档提供了设置 VibeCopilot 开发环境的详细步骤，确保团队成员能够使用一致的开发环境和配置。

## 1. 开发工具选择与配置

### 1.1 推荐的 IDE

VibeCopilot 项目推荐使用以下 IDE：

- **首选**: [Cursor](https://cursor.sh/)
  - 内置 AI 辅助功能，与 VibeCopilot 文档驱动开发理念最佳契合
  - 基于 VSCode，支持所有 VSCode 插件

- **备选**: [VS Code](https://code.visualstudio.com/)
  - 如果使用 VS Code，建议安装 GitHub Copilot 插件实现 AI 辅助功能

- **其他选项**: [Windsurf](https://getwindsurf.com/)
  - 另一款强大的 AI 辅助编程工具，与 VibeCopilot 兼容

### 1.2 必要插件安装

无论选择哪种 IDE，请安装以下插件：

#### 通用插件

- **EditorConfig**: 保持一致的编码样式
- **GitLens**: 增强 Git 功能
- **Markdown All in One**: 增强 Markdown 支持
- **Docker**: Docker 集成（如需要）

#### TypeScript 开发插件

- **TypeScript Hero**: 自动组织导入
- **ESLint**: 代码质量检查
- **Prettier**: 代码格式化
- **npm Intellisense**: npm 模块自动补全
- **Jest Runner**: 测试运行工具

### 1.3 配置同步

为确保团队成员使用一致的配置：

1. **Cursor/VS Code Settings Sync**:
   - 启用 Settings Sync 功能
   - 将团队配置上传到共享存储库

2. **项目级设置**:
   - 在项目根目录创建 `.vscode` 文件夹
   - 添加 `settings.json`、`extensions.json` 和 `launch.json`
   - 提交这些文件到代码库

## 2. 模块开发环境设置

根据 VibeCopilot 的模块化架构，不同模块可能需要特定的环境配置：

### 2.1 核心引擎模块

核心引擎是 VibeCopilot 的中央协调器，需要以下特定配置：

```bash
# 安装核心引擎依赖
npm install --save reflect-metadata rxjs inversify
```

确保在 `tsconfig.json` 中启用以下设置：

```json
{
  "compilerOptions": {
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true,
    "target": "ES2020"
  }
}
```

### 2.2 文档同步引擎模块

文档同步引擎需要以下额外配置：

```bash
# 安装文档处理相关依赖
npm install --save chokidar diff markdown-it gray-matter
```

### 2.3 AI规则生成器模块

AI规则生成器需要配置以下环境：

```bash
# 安装 AI 模型相关依赖
npm install --save langchain openai tiktoken
```

创建 AI 模型的环境变量：

```
OPENAI_API_KEY=your_api_key_here
AI_MODEL=gpt-4-turbo
```

### 2.4 GitHub集成模块

GitHub集成模块需要以下配置：

```bash
# 安装 GitHub API 客户端
npm install --save @octokit/rest @octokit/webhooks
```

设置 GitHub API 相关环境变量：

```
GITHUB_TOKEN=your_github_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret
```

### 2.5 工具连接器模块

工具连接器需要以下配置：

```bash
# 安装工具连接相关依赖
npm install --save socket.io node-ipc ws
```

### 2.6 Docusaurus发布系统模块

Docusaurus发布系统需要以下配置：

```bash
# 全局安装 Docusaurus CLI
npm install --global @docusaurus/cli

# 安装 Docusaurus 依赖
npm install --save @docusaurus/core @docusaurus/preset-classic
```

## 3. AI 规则配置

### 3.1 CursorRules 设置

1. **创建 AI 规则文件**:
   ```bash
   cp docs/ai/rules/cursor_rules_template.md .cursor.rules
   ```

2. **自定义规则**:
   - 编辑 `.cursor.rules` 文件，根据项目特定需求调整
   - 确保所有团队成员了解并遵循这些规则

3. **在 Cursor 中启用**:
   - 打开 Cursor 设置
   - 找到 "AI" 或 "CursorRules" 部分
   - 确保规则文件路径正确配置

### 3.2 AI 上下文配置

为确保 AI 工具（如 Cursor）能够访问必要的项目上下文：

1. **配置索引目录**:
   - 在 Cursor 设置中，配置 AI 应索引的目录
   - 确保核心文档目录 (`docs/`) 包含在索引范围内

2. **上下文管理最佳实践**:
   - 当讨论复杂功能时，总是引用相关文档
   - 使用连续性对话保持上下文
   - 对于大型项目，创建专门的上下文笔记

## 4. 项目知识库设置

### 4.1 核心文档目录结构

通过以下命令创建标准的文档结构：

```bash
mkdir -p docs/{ai,user,dev,shared}
mkdir -p docs/ai/{prompts,rules,roles}
mkdir -p docs/dev/{architecture,guides,references}
mkdir -p docs/shared/{templates,examples}
```

### 4.2 初始化核心文档

通过以下命令初始化核心文档：

```bash
# 从模板复制核心文档
cp docs/shared/templates/prd_template.md docs/dev/architecture/prd.md
cp docs/shared/templates/app_flow_template.md docs/dev/architecture/app_flow.md
cp docs/shared/templates/tech_stack_template.md docs/dev/architecture/tech_stack.md
cp docs/shared/templates/implementation_plan_template.md docs/dev/architecture/implementation_plan.md
```

## 5. 开发环境搭建

### 5.1 TypeScript 项目环境

```bash
# 初始化项目
npm init -y

# 安装 TypeScript
npm install --save-dev typescript ts-node @types/node

# 初始化 TypeScript 配置
npx tsc --init

# 创建基础项目结构
mkdir -p src/{core,document_sync,ai_rules,github,tool_connector,docusaurus,infrastructure}
```

### 5.2 安装项目依赖

```bash
# 安装核心依赖
npm install --save reflect-metadata rxjs inversify

# 安装工具依赖
npm install --save chokidar diff markdown-it gray-matter @octokit/rest

# 安装开发依赖
npm install --save-dev jest ts-jest @types/jest eslint prettier
```

### 5.3 环境变量配置

1. 创建环境变量模板：
   ```bash
   cp .env.example .env
   ```

2. 在 `.env` 文件中填写必要的环境变量：
   ```
   # 核心配置
   NODE_ENV=development

   # AI模型配置
   OPENAI_API_KEY=your_api_key_here
   AI_MODEL=gpt-4-turbo

   # GitHub配置
   GITHUB_TOKEN=your_github_token
   GITHUB_WEBHOOK_SECRET=your_webhook_secret

   # 文档同步配置
   SYNC_INTERVAL=5000
   OBSIDIAN_VAULT_PATH=/path/to/obsidian/vault

   # Docusaurus配置
   DOCUSAURUS_DEPLOY_URL=https://example.github.io/vibecopilot
   ```

3. 确保 `.env` 文件已添加到 `.gitignore`

### 5.4 Docker 开发环境（可选）

如果项目使用 Docker：

```bash
# 构建开发环境容器
docker-compose -f docker-compose.dev.yml build

# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 在容器内执行命令
docker-compose -f docker-compose.dev.yml exec app bash
```

## 6. 开发工具集成

### 6.1 代码质量工具

```bash
# 安装 ESLint 和 Prettier
npm install --save-dev eslint prettier eslint-config-prettier

# 初始化 ESLint
npx eslint --init

# 配置 Prettier
echo '{
  "semi": true,
  "trailingComma": "all",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}' > .prettierrc
```

### 6.2 测试工具设置

```bash
# 安装 Jest
npm install --save-dev jest ts-jest @types/jest

# 初始化 Jest 配置
npx jest --init

# 配置 ts-jest
echo 'module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  roots: ["<rootDir>/src", "<rootDir>/tests"],
  testMatch: ["**/__tests__/**/*.ts", "**/?(*.)+(spec|test).ts"],
  transform: {
    "^.+\\.tsx?$": "ts-jest"
  }
}' > jest.config.js
```

### 6.3 Git 钩子集成

```bash
# 安装 husky
npm install --save-dev husky lint-staged

# 初始化 husky
npx husky install

# 添加 pre-commit 钩子
npx husky add .husky/pre-commit "npx lint-staged"

# 配置 lint-staged
echo '{
  "*.{ts,tsx}": [
    "eslint --fix",
    "prettier --write"
  ],
  "*.{json,md}": [
    "prettier --write"
  ]
}' > .lintstagedrc
```

## 7. 模块开发检查清单

为确保模块开发的一致性，请遵循以下检查清单：

### 7.1 核心引擎模块

- [ ] 配置 TypeScript 装饰器支持
- [ ] 设置依赖注入容器
- [ ] 实现事件总线
- [ ] 配置日志系统

### 7.2 文档同步引擎模块

- [ ] 配置文件系统监控
- [ ] 设置 Markdown 解析器
- [ ] 配置文档转换器
- [ ] 测试文档同步功能

### 7.3 AI规则生成器模块

- [ ] 配置 OpenAI API 访问
- [ ] 设置规则模板目录
- [ ] 验证规则生成功能
- [ ] 测试规则部署

### 7.4 GitHub集成模块

- [ ] 配置 GitHub API 访问
- [ ] 设置 Webhook 处理器
- [ ] 测试仓库分析功能
- [ ] 验证文档与 Issues 同步

### 7.5 工具连接器模块

- [ ] 配置连接适配器
- [ ] 设置工具状态监控
- [ ] 测试工具连接功能
- [ ] 验证适配器注册系统

### 7.6 Docusaurus发布系统模块

- [ ] 安装 Docusaurus
- [ ] 配置内容转换器
- [ ] 设置部署流程
- [ ] 测试站点生成

## 8. 故障排除

### 8.1 常见问题

- **TypeScript 装饰器错误**: 检查 `tsconfig.json` 中的装饰器设置
- **依赖注入失败**: 确保正确注册和请求模块
- **环境变量配置错误**: 检查 `.env` 文件配置
- **模块通信问题**: 验证事件总线配置
- **GitHub API 限流**: 使用带有更高限额的 PAT 令牌

### 8.2 获取帮助

如遇到配置问题，请参考：

- 项目 Wiki 或 GitHub Issues
- 向团队技术负责人求助
- 参考 `docs/dev/guides/troubleshooting.md` 文档

## 9. 下一步

完成环境配置后，请：

1. 阅读 `docs/dev/architecture/prd.md` 了解项目需求
2. 查看 `docs/dev/architecture/functions.md` 了解功能设计
3. 参考 `docs/dev/architecture/modules.md` 掌握模块设计
4. 学习 `docs/dev/architecture/project_structure.md` 了解项目结构

---

如有任何问题或建议，请联系项目维护者。祝您开发愉快！
