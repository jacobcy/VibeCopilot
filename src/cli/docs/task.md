# 任务命令使用指南

任务命令用于管理项目中的任务（类似 GitHub issue）。提供了创建、查询、更新和删除等基本操作。

## 基本用法

### 列出任务

```bash
vibe task list [选项]
```

选项：

- `-s, --status`: 按状态过滤（可多选）
- `-a, --assignee`: 按负责人过滤
- `-l, --label`: 按标签过滤（可多选）
- `-r, --story`: 按关联的Story ID过滤
- `-i, --independent`: 仅显示独立任务（无Story关联）
- `--limit`: 限制返回数量
- `--offset`: 跳过指定数量的结果
- `-v, --verbose`: 显示更详细的信息
- `-f, --format`: 输出格式（yaml/json）

### 显示任务详情

```bash
vibe task show <任务ID或名称> [选项]
```

选项：

- `-v, --verbose`: 显示详细信息
- `-f, --format`: 输出格式（yaml/json）

### 创建任务

```bash
vibe task create [选项]
```

选项：

- `-t, --title`: 任务标题（必需）
- `-d, --desc`: 任务描述
- `-l, --labels`: 标签（逗号分隔）
- `-a, --assignee`: 负责人
- `-p, --priority`: 优先级（low/medium/high）
- `-f, --force`: 强制创建（允许同名任务）

### 更新任务

```bash
vibe task update <任务ID> [选项]
```

选项：

- `-t, --title`: 新标题
- `-d, --desc`: 新描述
- `-s, --status`: 新状态（todo/in_progress/review/done/blocked）
- `-a, --assignee`: 新负责人
- `-al, --add-labels`: 添加标签（逗号分隔）
- `-rl, --remove-labels`: 移除标签（逗号分隔）
- `-f, --force`: 强制更新

### 删除任务

```bash
vibe task delete <任务ID> [选项]
```

选项：

- `-f, --force`: 跳过确认直接删除

### 添加任务评论

```bash
vibe task comment <任务ID> [选项]
```

选项：

- `-c, --comment`: 要添加的评论（必需）

### 关联任务

```bash
vibe task link <任务ID> [选项]
```

选项：

- `-t, --type`: 关联类型（story/session/github）
- `-id, --target`: 目标ID（使用'-'解除关联）

## 输出格式

任务信息可以以YAML或JSON格式输出。默认使用YAML格式。

### YAML格式示例

```yaml
id: task_12345678
title: 实现任务管理功能
status: in_progress
assignee: alice
description: 开发任务的CRUD操作
labels: [feature, backend]
story_id: story_87654321
created_at: "2024-01-01T10:00:00"
updated_at: "2024-01-02T15:30:00"
```

### JSON格式示例

```json
{
  "id": "task_12345678",
  "title": "实现任务管理功能",
  "status": "in_progress",
  "assignee": "alice",
  "description": "开发任务的CRUD操作",
  "labels": ["feature", "backend"],
  "story_id": "story_87654321",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-02T15:30:00"
}
```

## 注意事项

1. 任务标题是唯一的，创建同名任务需要使用 `--force` 选项
2. 空值在YAML输出中统一显示为 `-`
3. 标签支持多个值，使用逗号分隔
4. 关联GitHub issue时，使用 `owner/repo#number` 格式
5. 任务状态变更会自动记录时间戳
6. 详细模式（`-v`）会显示更多任务信息
