# VibeCopilot 界面指南

VibeCopilot 提供两种不同的命令使用方式，分别针对不同的使用场景。本指南将帮助您理解这两种方式的区别和适用场景。

## 两种命令使用方式

### 1. Cursor IDE 中的智能助手命令（`/command`）

这种方式是在 Cursor IDE 的智能助手对话框中使用斜杠命令，例如 `/rule`、`/task` 等。

**特点：**

- 在 Cursor IDE 的聊天界面中使用
- 以斜杠（`/`）开头的命令
- 由 Cursor Rules 系统处理和路由
- 提供与 AI 助手的交互式体验

**实现方式：**

- 通过 `.cursor/rules/` 目录下的规则配置文件定义
- 规则定义了命令的解析和处理逻辑
- 由 AI 助手理解命令并调用本地接口

**示例：**

```
/rule create cmd git-commit --interactive
/task list --status=pending
```

### 2. 命令行工具（`vibecopilot`）

这种方式是直接在终端中使用 `vibecopilot` 命令行工具。

**特点：**

- 在系统终端中使用
- 标准命令行界面
- 直接调用本地代码，不依赖 AI 助手
- 适用于脚本和自动化场景

**实现方式：**

- 通过 Python CLI 模块实现
- 命令处理逻辑定义在 `src/cli/commands/` 目录
- 使用 `setup.py` 注册为系统命令

**示例：**

```bash
vibecopilot rule list
vibecopilot rule create cmd git-commit --vars='{"description":"Git提交规范"}'
```

## 文档索引

本文档目录包含以下内容：

1. [命令系统概述](command-system.md) - 命令系统的基本概念和架构
2. [命令开发指南](command-development.md) - 如何开发和扩展VibeCopilot命令
3. [术语表](glossary.md) - 重要概念和术语说明

## 选择合适的使用方式

- **在IDE内开发时**：使用 Cursor IDE 中的 `/command` 方式，获得AI辅助和上下文感知
- **自动化脚本**：使用命令行工具 `vibecopilot command`
- **频繁重复的操作**：命令行工具更高效
- **需要复杂分析或建议**：IDE内命令可提供更智能的响应

## 开始使用

请参阅各文档了解详细信息，或使用以下命令获取帮助：

```bash
# 命令行帮助
vibecopilot --help

# IDE内帮助
/help
```
