# 路线图命令使用指南

## 概述

路线图命令(`roadmap`)用于管理项目的路线图，支持创建、查看、更新、同步等操作。命令支持两种使用方式：

1. 规则命令：`/roadmap [subcommand] [options]`
2. 程序命令：`//roadmap [subcommand] [options]`

## 命令列表

### 1. 列出路线图元素 (list)

显示路线图中的元素（里程碑、故事、任务）。

```bash
roadmap list [type] [options]

# 参数
type                    # 元素类型 (all/milestone/story/task)，默认为all

# 选项
--status=<status>      # 筛选状态
    milestone: planned/in_progress/completed/cancelled
    story: planned/in_progress/completed/blocked
    task: todo/in_progress/review/done/blocked
--assignee=<user>      # 筛选指派人
--labels=<labels>      # 筛选标签（用逗号分隔）
--format=<format>      # 输出格式 (table/json/yaml)，默认为table
--sort=<field>         # 排序字段 (id/title/status/priority)
--desc                 # 降序排序
--page=<num>          # 页码，默认为1
--size=<num>          # 每页数量，默认为10

# 示例
roadmap list                                    # 列出所有元素
roadmap list task --status=in_progress         # 列出进行中的任务
roadmap list task --assignee=@dev1             # 列出指定用户的任务
roadmap list milestone --format=json           # 以JSON格式输出里程碑列表
roadmap list story --sort=priority --desc      # 按优先级降序列出故事
roadmap list task --labels=bug,urgent          # 列出带有特定标签的任务
```

### 2. 查看故事信息 (story)

查看路线图中的故事详细信息。

```bash
roadmap story [options]              # 列出所有故事
roadmap story <story_id> [options]   # 查看特定故事详情
roadmap story -m <milestone_id>      # 查看里程碑下的所有故事

# 选项
-m, --milestone <id>       # 指定里程碑ID
--format=<format>          # 输出格式 (table/json/yaml)，默认为table
--sort=<field>             # 排序字段 (id/title/status/priority/progress)
--desc                     # 降序排序
--assignee=<user>          # 筛选指派人
--labels=<labels>          # 筛选标签（用逗号分隔）
--status=<status>          # 筛选状态 (planned/in_progress/completed/blocked)

# 示例
roadmap story                                  # 列出所有故事
roadmap story S1                               # 查看特定故事详情
roadmap story -m M1                           # 查看里程碑下的所有故事
roadmap story --status=in_progress            # 列出进行中的故事
roadmap story --sort=priority --desc          # 按优先级降序列出故事
roadmap story S1 --format=json                # 以JSON格式输出故事详情
```

### 3. 创建路线图元素 (create)

创建新的路线图元素（里程碑、故事或任务）。

```bash
roadmap create <type> <title> [options]

# 参数
type                   # 元素类型 (milestone/story/task)
title                  # 元素标题

# 选项
--milestone=<id>      # 所属里程碑ID (用于story和task)
--priority=<level>    # 优先级 (P0-P3)
--desc=<text>  # 详细描述
--assignee=<user>     # 指派给用户
--labels=<labels>     # 标签列表，用逗号分隔

# 示例
roadmap create milestone "发布1.0版本" --desc="第一个正式版本发布"
roadmap create story "用户登录功能" --milestone=M1 --labels="功能,核心"
roadmap create task "设计用户界面" --milestone=M1 --priority=P1 --assignee=@dev1
roadmap create task "优化性能" --milestone=M2 --labels="优化,性能" --priority=P2
```

### 4. 更新路线图元素 (update)

更新路线图元素的状态。

```bash
roadmap update <type> <id> <status> [options]

# 参数
type                   # 元素类型 (milestone/story/task)
id                     # 元素ID
status                 # 新状态
    milestone: planned/in_progress/completed/cancelled
    story: planned/in_progress/completed/blocked
    task: todo/in_progress/review/done/blocked

# 选项
--sync               # 同步到GitHub
--comment=<text>    # 添加更新说明
--assignee=<user>   # 更新指派人
--labels=<labels>   # 更新标签（用逗号分隔）

# 示例
roadmap update milestone M1 in_progress --comment="开始实现核心功能"
roadmap update story S1 completed --sync
roadmap update task T1 in_progress --assignee=@dev2 --comment="开始编码"
roadmap update task T2 blocked --comment="等待依赖服务就绪" --labels="blocked,依赖"
```

### 5. 切换路线图 (switch)

切换或查看当前活跃的路线图。

```bash
roadmap switch [options]           # 显示当前活跃路线图
roadmap switch <roadmap_id>        # 切换到指定ID的路线图

# 参数
roadmap_id                         # 路线图ID，例如 roadmap_123

# 选项
--format=<format>                  # 输出格式 (table/json/yaml)，默认为table
--verbose                          # 显示详细信息

# 示例
roadmap switch                     # 显示当前活跃路线图和可用路线图列表
roadmap switch roadmap_123         # 切换到指定路线图
roadmap switch --verbose           # 显示详细的路线图信息
roadmap switch --format=json       # 以JSON格式输出路线图信息
```

### 6. 同步路线图 (sync)

在本地数据库和GitHub Project之间同步路线图数据。

```bash
roadmap sync <operation> [id]

# 参数
operation            # 同步操作类型 (push 或 pull)
id                  # push操作时为本地路线图ID，pull操作时为远程项目Number

# 选项
--verbose, -v       # 显示详细信息

# 示例
roadmap sync pull 123                # 从GitHub Project #123拉取到本地
roadmap sync push roadmap_456        # 将本地路线图 roadmap_456 推送到GitHub
roadmap sync push                    # 推送当前活动路线图到GitHub
roadmap sync pull 123 --verbose      # 显示详细的同步信息
```

**说明：**

- `pull` 操作会自动创建本地路线图（如果不存在）
- `push` 操作会自动创建远程GitHub Project（如果不存在）
- 不指定本地路线图ID时，将使用当前活动路线图
- 同步时会自动处理关联信息，无需手动设置
- 所有同步操作都是强制的，会直接覆盖目标端的数据

## 返回值格式

所有命令都返回统一格式的JSON响应：

```json
{
    "status": "success/error/warning",  # 执行状态
    "code": 0,                         # 状态码（0表示成功）
    "message": "执行结果描述",          # 描述信息
    "data": {                          # 返回数据
        // 命令特定的数据字段
    }
}
```

## 错误处理

当命令执行失败时，将返回错误信息：

```json
{
    "status": "error",
    "code": 1,
    "message": "错误描述",
    "data": null
}
```

## 最佳实践

1. **元素管理**：
   - 使用清晰的命名和描述
   - 及时更新元素状态
   - 合理使用标签和优先级
   - 指定合适的负责人

2. **路线图切换**：
   - 切换前确保当前工作已保存
   - 使用 `--verbose` 查看完整信息
   - 记录活跃路线图的ID

3. **故事管理**：
   - 为故事添加清晰的描述
   - 关联相关任务
   - 及时更新进度
   - 使用标签分类

4. **同步操作**：
   - 定期与GitHub同步以保持数据一致
   - 使用`--force`参数时需谨慎
   - 同步前确保本地更改已提交

5. **查询优化**：
   - 使用合适的筛选条件缩小结果范围
   - 合理设置分页参数避免返回过多数据
   - 选择合适的输出格式便于处理

6. **错误处理**：
   - 验证命令参数的正确性
   - 处理同步失败的情况
   - 保存错误日志以便追踪

## 相关文档

- [路线图同步指南](../roadmap_sync_guide.md)
- [路线图数据格式](../roadmap_data_format.md)
- [GitHub集成配置](../github_integration.md)
