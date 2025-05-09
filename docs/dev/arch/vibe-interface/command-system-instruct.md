# VibeCopilot 命令系统概述

本文档提供 VibeCopilot 命令系统的高级概述，包括系统架构、主要组件和两种命令方式。

## 命令系统架构

VibeCopilot 提供两种不同的命令使用方式，虽然它们有不同的用户界面，但共享许多底层代码：

```
┌────────────────────┐    ┌────────────────────┐
│   Cursor IDE 命令   │    │    命令行工具命令    │
│  (/rule, /task)    │    │(vibecopilot rule)  │
└─────────┬──────────┘    └──────────┬─────────┘
          │                          │
          ▼                          ▼
┌────────────────────┐    ┌────────────────────┐
│   Cursor Rules     │    │   命令解析器        │
│   (.cursor/rules/) │    │ (CommandParser)    │
└─────────┬──────────┘    └──────────┬─────────┘
          │                          │
          ▼                          ▼
┌────────────────────┐    ┌────────────────────┐
│   规则处理函数      │    │   命令处理器        │
│ (Rule Functions)   │    │ (Command Classes)  │
└─────────┬──────────┘    └──────────┬─────────┘
          │                          │
          └──────────────┬───────────┘
                         │
                         ▼
                ┌────────────────────┐
                │   核心业务逻辑      │
                │  (Core Services)   │
                └────────────────────┘
```

## 核心组件说明

### 命令行工具组件

1. **CLI 入口** (`src/cli/main.py`)
   - 命令行工具的主入口点
   - 接收命令行参数并路由到相应的命令处理器

2. **命令解析器** (`src/cli/command_parser.py`)
   - 解析命令行参数
   - 注册可用命令
   - 验证参数格式

3. **命令处理器** (`src/cli/commands/*.py`)
   - 每个命令一个处理器类
   - 实现具体命令逻辑
   - 例如：`RuleCommand`, `TaskCommand` 等

### Cursor IDE 命令组件

1. **Cursor Rules** (`.cursor/rules/`)
   - 定义 AI 助手如何理解和处理命令
   - 配置命令格式和参数
   - 定义命令响应模板

2. **规则处理函数** (通常使用 API 请求或本地函数)
   - 处理 Cursor IDE 中输入的命令
   - 连接 IDE 命令和核心业务逻辑

### 共享核心组件

1. **业务逻辑服务** (`src/core/`)
   - 实现实际功能的服务类
   - 由命令处理器和规则处理函数共同使用
   - 例如：`RuleManager`, `TaskManager` 等

2. **模型和数据结构** (`src/models/`)
   - 定义数据模型和结构
   - 确保两种命令方式使用一致的数据表示

## 两种命令方式的比较

| 特性 | Cursor IDE 命令 | 命令行工具 |
|------|----------------|-----------|
| 使用场景 | 在 IDE 中开发时 | 脚本和自动化 |
| 命令格式 | `/command --arg=value` | `vibecopilot command --arg=value` |
| 处理方式 | AI 助手 + 规则系统 | 直接执行本地代码 |
| 交互能力 | 可与 AI 对话交互 | 标准命令行交互 |
| 上下文感知 | 可感知编辑器上下文 | 仅限当前目录内容 |
| 实现位置 | `.cursor/rules/` | `src/cli/commands/` |

## 可用命令概览

VibeCopilot 提供以下主要命令：

1. **rule**: 规则管理命令
   - `list`: 列出规则
   - `create`: 创建规则
   - `show`: 显示规则详情
   - `delete`: 删除规则
   - `validate`: 验证规则

2. **task**: 任务管理命令
   - `list`: 列出任务
   - `create`: 创建任务
   - `update`: 更新任务状态
   - `delete`: 删除任务

3. **check**: 状态检查命令
   - `project`: 检查项目状态
   - `env`: 检查环境状态

更多命令及其详细用法，请参考各命令的具体文档。

## 文档索引

- [命令开发指南](command-development.md) - 详细的命令开发教程
- [术语表](glossary.md) - 关键概念和术语说明
- [README](README.md) - 界面使用指南
