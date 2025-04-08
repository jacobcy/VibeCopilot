# VibeCopilot 命令系统架构升级

本目录包含VibeCopilot新的命令系统架构规则，定义了改进的命令解析和执行机制。新系统引入了规则命令和程序命令的明确区分，以及基于模板的规则生成系统。

## 核心变更

1. **双轨命令系统**
   - `/command` - 规则命令，由Cursor Agent直接处理
   - `//command` - 程序命令，转换为`vibecopilot command`并通过终端执行

2. **模板化规则系统**
   - 规则从YAML/JSON源文件通过模板生成
   - 提供更好的结构化和变量支持
   - 支持版本控制和规则关联

3. **命令集成**
   - 集成vibecopilot命令行工具
   - 统一的流程和路线图管理
   - 结构化任务和知识库系统

## 规则文件清单

| 文件名 | 描述 |
|-------|------|
| `command-architecture.mdc` | 总体命令架构设计和原则 |
| `command-system.mdc` | 基础命令系统定义和规则 |
| `flow-command.mdc` | 工作流命令规则定义 |
| `roadmap-command.mdc` | 路线图命令规则定义 |
| `task-command.mdc` | 任务管理命令规则定义 |
| `memory-command.mdc` | 知识库命令规则定义 |
| `rule-command.mdc` | 规则管理命令规则定义 |
| `status-command.mdc` | 状态查看命令规则定义 |
| `template-system.mdc` | 模板系统架构和规则 |
| `rules-transition.mdc` | 规则系统过渡指南 |

## 使用说明

新的命令系统已经支持，可以通过以下两种格式使用命令：

```
# 规则命令（AI直接处理）
/rule list
/task create "新任务"
/help flow

# 程序命令（调用CLI工具）
//flow run dev:story
//roadmap show
//memory search "架构设计"
```

## 过渡说明

旧的命令格式仍然受支持，但我们建议开始使用新的命令格式以适应未来的变化。旧的规则文件已移至`/bak`目录，仅作参考。
