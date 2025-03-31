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

#### Python 项目插件
- **Python Extension**: Python 语言支持
- **Pylance**: 类型检查与智能提示
- **Python Docstring Generator**: 文档字符串生成器
- **Python Test Explorer**: 测试发现与执行

#### JavaScript/TypeScript 项目插件
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

## 2. AI 规则配置

### 2.1 CursorRules 设置

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

### 2.2 AI 上下文配置

为确保 AI 工具（如 Cursor）能够访问必要的项目上下文：

1. **配置索引目录**:
   - 在 Cursor 设置中，配置 AI 应索引的目录
   - 确保核心文档目录 (`docs/`) 包含在索引范围内

2. **上下文管理最佳实践**:
   - 当讨论复杂功能时，总是引用相关文档
   - 使用连续性对话保持上下文
   - 对于大型项目，创建专门的上下文笔记

## 3. 项目知识库设置

### 3.1 核心文档目录结构

通过以下命令创建标准的文档结构：

```bash
mkdir -p docs/{ai,user,dev,shared}
mkdir -p docs/ai/{prompts,rules,roles}
mkdir -p docs/dev/{architecture,guides,references}
mkdir -p docs/shared/{templates,examples}
```

### 3.2 初始化核心文档

通过以下命令初始化核心文档：

```bash
# 从模板复制核心文档
cp docs/shared/templates/prd_template.md docs/dev/architecture/prd.md
cp docs/shared/templates/app_flow_template.md docs/dev/architecture/app_flow.md
cp docs/shared/templates/tech_stack_template.md docs/dev/architecture/tech_stack.md
cp docs/shared/templates/frontend_guidelines_template.md docs/dev/guides/frontend_guidelines.md
cp docs/shared/templates/backend_structure_template.md docs/dev/guides/backend_structure.md
cp docs/shared/templates/implementation_plan_template.md docs/dev/architecture/implementation_plan.md
```

## 4. 开发环境搭建

### 4.1 Python 项目环境

```bash
# 使用 venv 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# 在 Windows 上:
.venv\Scripts\activate
# 在 macOS/Linux 上:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 4.2 JavaScript/TypeScript 项目环境

```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install

# 或使用 pnpm
pnpm install
```

### 4.3 环境变量配置

1. 创建环境变量模板：
   ```bash
   cp .env.example .env
   ```

2. 在 `.env` 文件中填写必要的环境变量

3. 确保 `.env` 文件已添加到 `.gitignore`

### 4.4 Docker 开发环境（可选）

如果项目使用 Docker：

```bash
# 构建开发环境容器
docker-compose -f docker-compose.dev.yml build

# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 在容器内执行命令
docker-compose -f docker-compose.dev.yml exec app bash
```

## 5. 开发工具集成

### 5.1 代码质量工具

#### Python 项目

```bash
# 安装代码质量工具
pip install black flake8 mypy isort pylint

# 配置 pre-commit
pip install pre-commit
pre-commit install
```

#### JavaScript/TypeScript 项目

```bash
# 安装 ESLint 和 Prettier
npm install --save-dev eslint prettier eslint-config-prettier

# 初始化 ESLint
npx eslint --init
```

### 5.2 测试工具设置

#### Python 项目

```bash
# 安装测试工具
pip install pytest pytest-cov

# 运行测试
pytest
```

#### JavaScript/TypeScript 项目

```bash
# 安装 Jest
npm install --save-dev jest ts-jest @types/jest

# 初始化 Jest 配置
npx jest --init
```

### 5.3 Git 钩子集成

创建 `.pre-commit-config.yaml` 文件：

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

# 针对 Python 项目
-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black

# 针对 JavaScript 项目
-   repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.38.0
    hooks:
    -   id: eslint
        files: \.(js|ts|jsx|tsx)$
        additional_dependencies:
        -   eslint@8.38.0
        -   eslint-config-prettier@8.8.0
```

## 6. 项目特定配置

### 6.1 工具链指南

根据项目具体技术栈，可能需要配置额外的工具：

- **前端框架** (React, Vue, Angular 等)
- **后端框架** (Django, Flask, Express 等)
- **数据库工具** (PostgreSQL, MongoDB 等)
- **CI/CD 工具** (GitHub Actions, Jenkins 等)

请参考项目的 `tech_stack.md` 文档了解具体需要配置的工具。

### 6.2 项目特定脚本

检查项目根目录下的 `scripts/` 文件夹，了解项目特定的工具脚本：

```bash
# 查看可用脚本
ls scripts/

# 执行特定脚本示例
./scripts/setup_dev_env.sh
```

## 7. 故障排除

### 7.1 常见问题

- **环境变量配置错误**: 检查 `.env` 文件配置
- **依赖冲突**: 尝试使用 `pip install --upgrade --force-reinstall -r requirements.txt`
- **插件不兼容**: 检查插件版本兼容性

### 7.2 获取帮助

如遇到配置问题，请参考：

- 项目 Wiki 或 GitHub Issues
- 向团队技术负责人求助
- 参考 `docs/dev/guides/troubleshooting.md` 文档

## 8. 下一步

完成环境配置后，请：

1. 阅读 `docs/dev/architecture/prd.md` 了解项目需求
2. 查看 `docs/user/workflow.md` 熟悉工作流程
3. 参考 `docs/ai/rules/cursor_rules_template.md` 了解 AI 工具使用规范

---

如有任何问题或建议，请联系项目维护者。祝您开发愉快！
