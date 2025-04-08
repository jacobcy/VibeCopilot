---
title: VibeCopilot 规则模板使用指南
description: 本文档介绍如何使用VibeCopilot的规则模板系统
author: VibeCopilot Team
date: 2024-04-03
---

# VibeCopilot 规则模板使用指南

## 目录

1. [简介](#简介)
2. [规则模板类型](#规则模板类型)
3. [命令行使用方法](#命令行使用方法)
4. [对话界面使用方法](#对话界面使用方法)
5. [最佳实践](#最佳实践)
6. [常见问题](#常见问题)

## 简介

VibeCopilot的规则模板系统是一个强大的工具，它能帮助您：

- 快速创建符合项目标准的规则
- 保持规则格式的一致性
- 自动化规则生成过程
- 提高开发效率

## 规则模板类型

VibeCopilot提供以下几种规则模板：

1. **命令规则模板** (`cmd_rule.md`)
   - 用于创建命令处理规则
   - 适用于定义新的命令行为
   - 包含命令格式、参数说明和执行流程

2. **自动规则模板** (`auto_rule.md`)
   - 用于创建自动应用的规则
   - 基于文件类型自动触发
   - 适用于代码风格、格式化等场景

3. **流程规则模板** (`flow_rule.md`)
   - 用于创建开发流程规则
   - 定义开发生命周期中的检查点
   - 确保流程规范性

4. **角色规则模板** (`role_rule.md`)
   - 用于创建专家角色规则
   - 定义特定领域专家的行为模式
   - 提供专业化的辅助能力

5. **代理规则模板** (`agent_rule.md`)
   - 用于创建AI代理规则
   - 控制AI助手的行为方式
   - 实现特定场景下的智能辅助

6. **最佳实践规则模板** (`best_practices_rule.md`)
   - 用于创建最佳实践规则
   - 定义编码标准和开发规范
   - 提供质量保证指导

## 命令行使用方法

### 1. 创建规则

使用`vibecopilot`命令行工具创建规则：

```bash
# 创建新规则
vibecopilot rule create [选项] <模板类型> <规则名称>

# 选项说明：
#   --template-dir   指定模板目录
#   --output-dir     指定输出目录
#   --vars          指定变量值（JSON格式）
#   --interactive   使用交互模式

# 示例：创建命令规则
vibecopilot rule create cmd git-commit --interactive

# 示例：使用变量创建规则
vibecopilot rule create agent code-review \
  --vars '{"description": "代码审查专家", "purpose": "提供专业的代码审查建议"}'
```

### 2. 管理规则

```bash
# 列出所有规则
vibecopilot rule list [--type <类型>]

# 查看规则详情
vibecopilot rule show <规则ID>

# 编辑规则
vibecopilot rule edit <规则ID>

# 删除规则
vibecopilot rule delete <规则ID>

# 导出规则
vibecopilot rule export <规则ID> [输出路径]

# 导入规则
vibecopilot rule import <规则文件路径>
```

### 3. 规则验证

```bash
# 验证规则语法
vibecopilot rule validate <规则ID>

# 检查规则冲突
vibecopilot rule check-conflicts <规则ID>
```

## 对话界面使用方法

在Cursor编辑器中，您可以通过对话命令管理规则：

### 1. 创建规则

使用`/rule create`命令创建新规则：

```
/rule create <规则类型> <规则名称>
```

例如：

```
/rule create cmd git-commit
```

### 2. 编辑规则

```
/rule edit <规则ID>
```

### 3. 应用规则

规则创建后会根据其类型自动应用：

- 自动规则：基于文件类型自动应用
- 命令规则：通过`/命令名`触发
- 流程规则：在开发流程中自动检查
- 角色规则：在相关场景自动激活

### 4. 查看和管理规则

```
# 列出规则
/rule list [类型]

# 删除规则
/rule delete <规则ID>

# 检查规则
/rule check <规则ID>

# 调试规则
/rule debug <规则ID>
```

## 最佳实践

1. **规则命名约定**
   - 使用描述性名称
   - 遵循kebab-case命名方式
   - 添加适当的前缀标识规则类型

2. **规则组织**
   - 按功能域组织规则
   - 保持规则之间的独立性
   - 避免规则间的循环依赖

3. **规则维护**
   - 定期审查和更新规则
   - 删除过时的规则
   - 保持规则文档的更新

4. **规则测试**
   - 创建规则后进行测试
   - 验证规则的触发条件
   - 确保规则行为符合预期

## 常见问题

### Q1: 如何选择合适的规则模板？

根据您的需求选择：

- 需要新命令？使用cmd_rule
- 需要自动化操作？使用auto_rule
- 需要流程控制？使用flow_rule
- 需要专家角色？使用role_rule

### Q2: 规则之间有冲突怎么办？

系统会自动检测规则冲突，如果发现冲突：

1. 使用命令行工具检查：`vibecopilot rule check-conflicts <规则ID>`
2. 或在对话界面使用：`/rule check <规则ID>`
3. 根据提示调整规则优先级或修改规则内容

### Q3: 如何在CI/CD中使用规则？

1. 使用命令行工具：

```bash
# 在CI/CD脚本中验证规则
vibecopilot rule validate --all

# 导出规则用于其他环境
vibecopilot rule export-all rules.zip
```

2. 使用API集成（需要额外配置）：

```bash
# 安装API依赖
pip install vibecopilot[api]

# 启动API服务
vibecopilot api start
```

## 更多资源

- [规则模板开发指南](/docs/dev/rule_template)
- [规则示例集合](/examples/rules)
- [常见规则模式](/docs/patterns/rules)
- [API文档](/docs/api/rules)
