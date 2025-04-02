# VibeCopilot 开发环境配置指南

> **文档元数据**
> 版本: 2.0
> 上次更新: 2024-04-25
> 负责人: 技术架构团队

本文档提供设置VibeCopilot开发环境的简明步骤，确保团队成员能够快速配置开发环境。

## 1. 开发工具安装

### 1.1 核心工具

VibeCopilot项目开发需要以下核心工具：

- **Cursor**: <https://cursor.sh/>
  - 内置AI辅助功能，支持规则系统
  - 主要代码编辑环境

- **Python 3.8+**: <https://www.python.org/downloads/>
  - 脚本开发的核心语言
  - 建议使用最新稳定版

- **Git**: <https://git-scm.com/downloads>
  - 版本控制系统
  - 用于规则和脚本管理

### 1.2 推荐插件与扩展

#### Cursor/VS Code插件

- **Python**: Python语言支持
- **Markdown All in One**: 增强Markdown编辑能力
- **GitLens**: 增强Git功能
- **Mermaid Preview**: 预览流程图
- **YAML**: YAML文件支持

## 2. 项目环境设置

### 2.1 仓库克隆

```bash
# 克隆项目仓库
git clone https://github.com/your-username/VibeCopilot.git
cd VibeCopilot
```

### 2.2 Python环境配置

推荐使用虚拟环境管理依赖：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 激活虚拟环境 (macOS/Linux)
source venv/bin/activate

# 安装项目依赖
pip install -r requirements.txt
```

### 2.3 环境变量配置

创建`.env`文件并配置必要的环境变量：

```bash
# 复制环境变量模板
cp .env.example .env
```

编辑`.env`文件，配置以下内容：

```
# 基础配置
ENVIRONMENT=development
LOG_LEVEL=info

# GitHub集成
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your-username/VibeCopilot

# Obsidian集成
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

# Basic Memory集成
BASIC_MEMORY_API_KEY=your_api_key
```

## 3. 规则系统设置

### 3.1 Cursor规则配置

VibeCopilot使用Cursor的规则系统进行AI行为控制：

1. **在Cursor中配置规则目录**:
   - 打开Cursor设置
   - 找到AI或自定义代理设置
   - 配置规则目录指向项目的`rules`目录

2. **规则结构检查**:
   ```bash
   # 检查规则目录结构
   ls -la rules/

   # 确保各类规则目录存在
   ls -la rules/core-rules/
   ls -la rules/command-rules/
   ls -la rules/flow-rules/
   ```

### 3.2 规则模板使用

创建新规则时，使用规则模板：

```bash
# 复制规则模板创建新规则
cp templates/rules/command_rule_template.mdc rules/command-rules/new-command.mdc

# 根据需要编辑规则文件
```

## 4. 集成工具配置

### 4.1 GitHub 配置

1. **创建个人访问令牌 (PAT)**:
   - 访问 GitHub 设置 → 开发者设置 → 个人访问令牌
   - 创建具有repo权限的令牌
   - 将令牌添加到`.env`文件的`GITHUB_TOKEN`变量

2. **验证GitHub连接**:
   ```bash
   # 测试GitHub连接
   python scripts/main.py github test-connection
   ```

### 4.2 Obsidian 配置

1. **创建或选择知识库**:
   - 打开Obsidian，创建或打开现有知识库
   - 记录知识库路径

2. **配置知识库路径**:
   - 将知识库路径添加到`.env`文件的`OBSIDIAN_VAULT_PATH`变量
   - 确保路径使用绝对路径格式

3. **验证Obsidian连接**:
   ```bash
   # 测试Obsidian连接
   python scripts/main.py obsidian test-connection
   ```

### 4.3 Basic Memory 配置

如果使用Basic Memory作为长期记忆系统：

1. **获取API密钥**:
   - 申请Basic Memory API密钥
   - 将密钥添加到`.env`文件的`BASIC_MEMORY_API_KEY`变量

2. **验证Memory连接**:
   ```bash
   # 测试Memory连接
   python scripts/main.py memory test-connection
   ```

## 5. 命令测试与使用

VibeCopilot使用命令系统操作各种功能：

```bash
# 查看帮助
python scripts/main.py help

# 测试计划命令
python scripts/main.py plan list

# 测试任务命令
python scripts/main.py task list
```

## 6. 常见问题解决

### 6.1 环境问题

- **规则不生效**:
  - 确认规则目录配置正确
  - 检查规则文件格式是否符合MDC标准
  - 重启Cursor应用规则变更

- **Python依赖问题**:
  - 确保虚拟环境已激活
  - 更新依赖: `pip install -r requirements.txt --upgrade`
  - 检查Python版本兼容性

- **API集成问题**:
  - 验证API密钥是否正确
  - 检查网络连接
  - 查看集成日志: `logs/integrations.log`

### 6.2 获取帮助

如遇问题，可通过以下方式获取支持：

- 查阅`docs/user/guide/troubleshooting.md`
- 提交GitHub Issues
- 使用`/help`命令获取内置帮助

## 7. 下一步

完成环境配置后，建议:

1. 查看`docs/dev/architecture/0_overview.md`了解项目概览
2. 学习`docs/dev/architecture/7_workflow.md`了解工作流程
3. 参考`docs/dev/architecture/9_workflow_guide.md`掌握使用方法
4. 尝试使用`/help`命令了解所有可用功能

---

如有任何问题或建议，请联系项目维护者。
