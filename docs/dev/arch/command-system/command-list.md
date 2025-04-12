# VibeCopilot 命令系统命令表（标准化版）

## 命令系统定位说明

VibeCopilot命令系统作为工作流解释器，主要职责是：

1. **工作流解释**：
   - 解释和理解工作流定义
   - 提供工作流上下文分析
   - 生成下一步建议
   - 不直接执行具体操作

2. **状态追踪**：
   - 维护工作流会话状态
   - 记录执行进度
   - 提供可视化支持
   - 管理会话生命周期

3. **协调角色**：
   - 连接用户意图和系统功能
   - 提供自然语言理解
   - 转换命令格式
   - 管理执行上下文

## 命令表

| 命令类别 | 命令名称 | 子命令 | 描述 | 用法示例 |
|---------|---------|-------|------|---------|
| **规则管理** | rule | | 规则管理命令 | |
| | | list | 列出所有规则 | `vibecopilot rule list [--type=<rule_type>] [--verbose]` |
| | | show | 显示规则详情 | `vibecopilot rule show <id> [--format=<json\|text>]` |
| | | create | 创建新规则 | `vibecopilot rule create <template_type> <name> [--vars=<json>]` |
| | | update | 更新规则 | `vibecopilot rule update <id> [--vars=<json>]` |
| | | delete | 删除规则 | `vibecopilot rule delete <id> [--force]` |
| | | validate | 验证规则 | `vibecopilot rule validate <id> [--all]` |
| | | export | 导出规则 | `vibecopilot rule export <id> [--output=<path>] [--format=<format>]` |
| | | import | 导入规则 | `vibecopilot rule import <file_path> [--overwrite]` |
| **工作流定义** | flow | | 工作流定义管理命令 | |
| | | list | 列出所有工作流定义 | `vibecopilot flow list [--type=<workflow_type>] [--verbose]` |
| | | show | 查看工作流定义详情 | `vibecopilot flow show --id=<id> [--format=<json\|text>]` |
| | | create | 创建工作流定义 | `vibecopilot flow create --source=<path> [--template=<template>] [--name=<name>]` |
| | | update | 更新工作流定义 | `vibecopilot flow update --id=<id> [--name=<name>]` |
| | | delete | 删除工作流定义 | `vibecopilot flow delete --id=<id> [--force]` |
| | | export | 导出工作流定义 | `vibecopilot flow export --id=<id> [--format=<json\|yaml>] [--output=<path>]` |
| | | import | 导入工作流定义 | `vibecopilot flow import --file=<path> [--overwrite]` |
| | | context | 获取工作流阶段上下文 | `vibecopilot flow context [--stage=<stage_id>] [--session=<session_id>]` |
| | | next | 获取下一阶段建议 | `vibecopilot flow next [--session=<session_id>] [--current=<stage_id>]` |
| | | validate | 验证工作流一致性 | `vibecopilot flow validate [--id=<id>] [--fix]` |
| | | visualize | 可视化工作流结构 | `vibecopilot flow visualize --id=<id> [--format=<mermaid\|dot>]` |
| **工作流会话** | flow session | | 工作流会话管理命令 | |
| | | list | 列出所有会话 | `vibecopilot flow session list [--format=<json\|text>]` |
| | | show | 显示会话详情 | `vibecopilot flow session show --id=<id> [--format=<json\|text>]` |
| | | create | 创建并启动新会话 | `vibecopilot flow session create --workflow=<workflow_id> [--name=<name>]` |
| | | close | 结束会话 | `vibecopilot flow session close --id=<id> [--force]` |
| | | switch | 切换当前活动会话 | `vibecopilot flow session switch --id=<id>` |
| | | update | 更新会话属性 | `vibecopilot flow session update --id=<id> [--name=<name>]` |
| | | delete | 永久删除会话 | `vibecopilot flow session delete --id=<id> [--force]` |
| **路线图管理** | roadmap | | 路线图管理命令 | |
| | | list | 列出所有路线图 | `vibecopilot roadmap list [--verbose]` |
| | | show | 查看路线图详情 | `vibecopilot roadmap show <id> [--format=<json\|text>]` |
| | | create | 创建路线图 | `vibecopilot roadmap create --name=<name> [--desc=<description>]` |
| | | update | 更新路线图 | `vibecopilot roadmap update <id> [--name=<name>] [--desc=<description>]` |
| | | delete | 删除路线图 | `vibecopilot roadmap delete <id> [--force]` |
| | | sync | 同步路线图数据 | `vibecopilot roadmap sync [--source=<source>] [--verbose]` |
| | | switch | 切换活动路线图 | `vibecopilot roadmap switch <id>` |
| | | status | 查看路线图状态 | `vibecopilot roadmap status <id>` |
| **任务管理** | task | | 任务管理命令（类似GitHub issue） | |
| | | list | 列出所有任务 | `vibecopilot task list [--status=<status>] [--assignee=<assignee>] [--verbose]` |
| | | show | 查看任务详情 | `vibecopilot task show <id> [--format=<json\|text>]` |
| | | create | 创建任务 | `vibecopilot task create --title=<title> [--desc=<description>] [--assignee=<assignee>]` |
| | | update | 更新任务 | `vibecopilot task update <id> [--status=<status>] [--assignee=<assignee>]` |
| | | delete | 删除任务 | `vibecopilot task delete <id> [--force]` |
| | | link | 关联任务到其他实体 | `vibecopilot task link <id> --target=<target_id> --type=<link_type>` |
| | | comment | 添加任务评论 | `vibecopilot task comment <id> --content=<content>` |
| **状态视图** | status | | 项目状态管理命令 | |
| | | show | 显示项目状态概览 | `vibecopilot status show [--type=<status_type>] [--verbose]` |
| | | flow | 显示流程状态 | `vibecopilot status flow [--verbose]` |
| | | roadmap | 显示路线图状态 | `vibecopilot status roadmap [--verbose]` |
| | | task | 显示任务状态 | `vibecopilot status task [--verbose]` |
| | | update | 更新项目阶段 | `vibecopilot status update --phase=<phase>` |
| | | init | 初始化项目状态 | `vibecopilot status init [--name=<project_name>]` |
| **记忆管理** | memory | | 知识库管理命令 | |
| | | list | 列出知识库内容 | `vibecopilot memory list [--folder=<folder>] [--verbose]` |
| | | show | 显示知识库内容详情 | `vibecopilot memory show <path> [--format=<json\|text>]` |
| | | create | 创建知识库内容 | `vibecopilot memory create --title=<title> --folder=<folder> [--content=<content>]` |
| | | update | 更新知识库内容 | `vibecopilot memory update <path> [--content=<content>]` |
| | | delete | 删除知识库内容 | `vibecopilot memory delete <path> [--force]` |
| | | search | 搜索知识库 | `vibecopilot memory search --query=<query> [--type=<content_type>]` |
| | | import | 导入到知识库 | `vibecopilot memory import <source_dir> [--recursive]` |
| | | export | 导出知识库 | `vibecopilot memory export [--output=<output_dir>] [--format=<format>]` |
| | | sync | 同步知识库 | `vibecopilot memory sync <sync_type> [--verbose]` |
| **数据库管理** | db | | 数据库管理命令 | |
| | | init | 初始化数据库 | `vibecopilot db init [--force]` |
| | | list | 列出数据库内容 | `vibecopilot db list --type=<entity_type> [--verbose]` |
| | | show | 显示数据库条目 | `vibecopilot db show --type=<entity_type> --id=<id> [--format=<json\|text>]` |
| | | create | 创建数据库条目 | `vibecopilot db create --type=<entity_type> --data=<json_data>` |
| | | update | 更新数据库条目 | `vibecopilot db update --type=<entity_type> --id=<id> --data=<json_data>` |
| | | delete | 删除数据库条目 | `vibecopilot db delete --type=<entity_type> --id=<id> [--force]` |
| | | query | 查询数据 | `vibecopilot db query --type=<entity_type> [--query=<query>]` |
| | | backup | 备份数据库 | `vibecopilot db backup [--output=<path>]` |
| | | restore | 恢复数据库 | `vibecopilot db restore <backup_file> [--force]` |
| **模板管理** | template | | 模板管理命令 | |
| | | list | 列出所有模板 | `vibecopilot template list [--type=<template_type>] [--verbose]` |
| | | show | 查看模板详情 | `vibecopilot template show <id> [--format=<json\|text>]` |
| | | create | 创建模板 | `vibecopilot template create --name=<name> --type=<template_type> --content=<content> [--desc=<description>]` |
| | | update | 更新模板 | `vibecopilot template update <id> [--name=<name>] [--content=<content>] [--desc=<description>]` |
| | | delete | 删除模板 | `vibecopilot template delete <id> [--force]` |
| | | import | 导入模板 | `vibecopilot template import <file_path> [--overwrite] [--recursive]` |
| | | export | 导出模板 | `vibecopilot template export <id> [--output=<path>] [--format=<format>]` |
| | | generate | 根据模板生成文件 | `vibecopilot template generate <id> <output_file> [--vars=<json>]` |
| | | init | 初始化模板库 | `vibecopilot template init [--force] [--source=<dir>]` |
| **帮助系统** | help | | 帮助命令 | `vibecopilot help [command] [--verbose]` |

## 命令设计说明

1. **工作流解释器定位**：
   - 命令系统专注于解释和理解工作流
   - 不直接执行业务逻辑，而是提供执行建议
   - 维护工作流状态和上下文
   - 协助用户理解和决策

2. **标准化子命令集**：
   - 所有主命令使用统一的核心子命令：`list`, `show`, `create`, `update`, `delete`
   - 特殊子命令在基础集之外增加，确保逻辑清晰
   - 将`view`统一为`show`，保持一致性

3. **命令/参数风格统一**：
   - 长选项统一使用`--参数名=值`格式
   - 所有命令支持`--verbose`选项，提供详细输出
   - 危险操作（如删除）支持`--force`选项
   - 输出格式控制统一使用`--format=<json|text>`

4. **工作流定义与会话分离**：
   - 明确区分工作流定义和工作流会话：
     - 工作流定义：静态模板，描述可用阶段及其特性
     - 工作流会话：动态实例，表示解释中的工作流及其状态
   - `flow`命令主要管理工作流定义（创建、更新模板）
   - `flow session`命令管理工作流会话（创建、切换、关闭会话）
   - 通过`context`和`next`提供解释和建议

5. **工作流会话持久化**：
   - 会话支持完整的生命周期管理
   - 允许在同一会话中保持上下文连续性
   - 提供会话切换和状态追踪
   - 支持会话属性的动态更新

6. **错误处理增强**：
   - 所有命令支持统一的错误输出格式
   - 详细模式（`--verbose`）提供更多错误上下文
   - 错误发生时提供可能的解决方案建议
   - 示例：`❌ 创建会话失败: 工作流定义无效。建议: 请使用 'vibecopilot flow validate' 检查工作流定义`

7. **进度显示**：
   - 长时间运行的命令显示解释进度
   - 使用统一的进度格式：`[===>    ] 30% 正在分析...`
   - 完成后显示总结信息：`✅ 已解释 15 个阶段，发现 3 个潜在问题`

8. **向后兼容**：
   - 保留原有命令别名，确保不破坏现有脚本
   - 逐步引导用户使用新格式
   - 在使用旧命令时提示新命令格式

9. **Agent调用支持**：

- 所有命令默认支持`--agent-mode`选项，启用agent优化的输出格式
- 命令输出为结构化JSON，包含状态码和明确的下一步操作建议
- 错误信息包含明确的代码和可行的纠正建议
- 支持Agent进度跟踪和异步操作状态查询

## Agent调用规范

所有命令在Agent模式下输出标准化JSON：

```json
{
  "status": "success|error|warning|info",
  "code": 0,
  "message": "操作结果简要描述",
  "data": {
    // 命令特定的数据
  },
  "interpretation": {
    "context": "当前上下文描述",
    "suggestions": [
      {
        "action": "建议的后续动作",
        "reason": "建议原因"
      }
    ]
  }
}
```
