# VibeCopilot 命令系统命令表（标准化版）

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
| | | show | 查看工作流定义详情 | `vibecopilot flow show <id> [--format=<json\|text>]` |
| | | create | 创建工作流定义 | `vibecopilot flow create <workflow_type> [--name=<name>] [--desc=<description>]` |
| | | update | 更新工作流定义 | `vibecopilot flow update <id> [--name=<name>] [--desc=<description>]` |
| | | export | 导出工作流定义 | `vibecopilot flow export <id> [--format=<format>] [--output=<path>]` |
| | | import | 导入工作流定义 | `vibecopilot flow import <file_path> [--overwrite]` |
| | | run | 运行工作流阶段（开始执行） | `vibecopilot flow run <workflow_name>:<stage_name> [--name=<name>] [--session=<session_id>]` |
| | | context | 获取工作流阶段上下文 | `vibecopilot flow context <workflow_id> <stage_id>` |
| | | next | 获取下一阶段建议 | `vibecopilot flow next <workflow_id> <stage_id>` |
| | | visualize | 可视化工作流结构 | `vibecopilot flow visualize <id> [--format=mermaid]` |
| **工作流会话** | flow session | | 工作流会话管理命令 | |
| | | list | 列出所有会话实例 | `vibecopilot flow session list [--status=<status>] [--workflow=<workflow_id>] [--verbose]` |
| | | show | 查看会话详情和进度 | `vibecopilot flow session show <id> [--format=<json\|text>]` |
| | | create | 创建新的工作流会话实例 | `vibecopilot flow session create <workflow_id> [--name=<name>]` |
| | | pause | 暂停工作流会话执行 | `vibecopilot flow session pause <id>` |
| | | resume | 恢复暂停的会话执行 | `vibecopilot flow session resume <id>` |
| | | abort | 终止工作流会话执行 | `vibecopilot flow session abort <id>` |
| | | delete | 删除工作流会话记录 | `vibecopilot flow session delete <id> [--force]` |
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
| **帮助系统** | help | | 帮助命令 | `vibecopilot help [command] [--verbose]` |

## 命令设计说明

1. **标准化子命令集**：
   - 所有主命令都使用统一的核心子命令：`list`, `show`, `create`, `update`, `delete`
   - 特殊子命令在基础集之外增加，确保逻辑清晰
   - 将`view`统一为`show`，保持一致性

2. **命令/参数风格统一**：
   - 长选项统一使用`--参数名=值`格式
   - 所有命令支持`--verbose`选项，提供详细输出
   - 危险操作（如删除）支持`--force`选项
   - 输出格式控制统一使用`--format=<json|text>`

3. **任务管理独立化**：
   - 将`task`提升为顶级命令，类似GitHub issue系统
   - 可以独立于完整roadmap工作
   - 添加评论和关联功能，增强协作能力

4. **状态视图关联性**：
   - 将`status`定位为各系统状态的视图层
   - 通过子命令关联到`flow`、`roadmap`和`task`
   - 提供统一的状态查看入口

5. **工作流定义与会话分离**：
   - 明确区分工作流定义和工作流会话：
     - 工作流定义：静态模板，描述可用阶段及其特性
     - 工作流会话：动态实例，表示执行中的工作流及其状态
   - `flow`命令主要管理工作流定义（创建、更新模板）
   - `flow session`命令管理工作流执行实例（创建、暂停、恢复会话）
   - `flow run`是连接定义和会话的桥梁，它可以在现有会话中执行或创建新会话

6. **工作流会话持久化**：
   - 会话支持完整的生命周期管理（创建、暂停、恢复、完成、终止）
   - 允许在同一会话中执行多个阶段，保持上下文连续性
   - 支持通过`--session`参数在已有会话中运行阶段
   - 提供会话进度跟踪和阶段完成度显示

7. **错误处理增强**：
   - 所有命令支持统一的错误输出格式
   - 详细模式（`--verbose`）提供更多错误上下文
   - 错误发生时提供可能的解决方案建议
   - 示例：`❌ 创建任务失败: 无法连接数据库。建议: 请检查数据库连接或运行 'vibecopilot db init'`

8. **进度显示**：
   - 长时间运行的命令（如同步、导入）显示进度
   - 使用统一的进度格式：`[===>    ] 30% 正在处理...`
   - 完成后显示总结信息：`✅ 已同步 15 个文件，跳过 3 个文件，用时 5 秒`

9. **向后兼容**：
   - 保留原有命令别名，确保不破坏现有脚本
   - 逐步引导用户使用新格式
   - 在使用旧命令时提示新命令格式

10. **Agent调用支持**：

- 所有命令默认支持`--agent-mode`选项，启用agent优化的输出格式
- 命令输出为结构化JSON，包含状态码和明确的下一步操作建议
- 错误信息包含明确的代码和可行的纠正建议
- 支持Agent进度跟踪和异步操作状态查询

## Agent调用规范

### 输出格式

所有命令在Agent模式下输出标准化JSON：

```json
{
  "status": "success|error|warning|info",
  "code": 0,
  "message": "操作结果简要描述",
  "data": {
    // 命令特定的数据
  },
  "next_actions": [
    {
      "command": "建议的后续命令",
      "description": "命令的作用描述"
    }
  ]
}
```
