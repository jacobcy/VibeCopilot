# VibeCopilot AI 文档

本目录包含**专为AI工具直接阅读**的指令和规则文档，这些文档会被自动同步到 `.cursor/rules` 目录，作为AI工具的上下文信息。

## 文档范围界定

AI文档目录仅应包含以下类型的内容：

- **AI行为规则**：直接指导AI如何理解和处理代码
- **项目结构规范**：提供项目架构和文件组织的指导
- **提示词模板**：AI可引用的标准提示词模板
- **上下文信息**：帮助AI理解项目当前状态的信息

**不应包含**的内容（这些应移至dev/user目录）：

- 面向人类开发者的详细技术指南
- 项目完整API文档
- 学习教程和使用说明
- 完整架构设计和技术选型理由

## 目录结构

- `prompts/`: AI提示词模板和场景化指令
- `context/`: 项目上下文信息，帮助AI理解项目状态
- `rules/`: AI行为规则和开发约束
- `references/`: AI需要参考的精简技术信息

## 文档同步机制

项目使用 `scripts/sync_ai_docs.py` 脚本将本目录下的文档自动同步到 `.cursor/rules` 目录，转换为Cursor规则文件。

### 同步规则

- `rules/*.md` → `.cursor/rules/rule_*.mdc`
- `prompts/*.md` → `.cursor/rules/prompt_*.mdc`
- `context/*.md` → `.cursor/rules/context_*.mdc`
- `references/*.md` → `.cursor/rules/ref_*.mdc`

### 手动同步

```bash
python scripts/sync_ai_docs.py
```

### 自动同步

该脚本可以集成到Git钩子中，实现自动同步：

```bash
# 在 .git/hooks/pre-commit 中添加
python scripts/sync_ai_docs.py
```

## 文档编写指南

1. 直接以AI为受众，使用指令性语言
2. 保持简洁，避免冗长解释
3. 提供明确的规则而非开放式建议
4. 包含具体示例而非抽象概念
5. 使用标准文档模板并包含适当的元数据
