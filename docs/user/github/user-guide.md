# GitHub集成 用户指南

## 简介

VibeCopilot 提供了与 GitHub 的深度集成，使您能够从命令行界面轻松管理您的 GitHub 项目。本指南将帮助您了解如何使用 VibeCopilot 的 GitHub 集成功能。

## 前提条件

在使用 GitHub 集成功能前，您需要：

1. 安装并配置 VibeCopilot
2. 有一个有效的 GitHub 账户
3. 配置 GitHub 个人访问令牌（在首次使用时会提示设置）

## 基本命令

### 项目管理

```bash
# 查看项目列表
/github list projects

# 查看项目详情
/github show project <项目名称>

# 创建新项目
/github create project <项目名称> --description="项目描述"

# 删除项目
/github delete project <项目名称>
```

### Issue 管理

```bash
# 查看 issues 列表
/github list issues --project=<项目名称>

# 创建新 issue
/github create issue --project=<项目名称> --title="Issue标题" --body="Issue详细描述"

# 关闭 issue
/github close issue <issue编号> --project=<项目名称>
```

### Pull Request 管理

```bash
# 查看 PR 列表
/github list prs --project=<项目名称>

# 创建新 PR
/github create pr --project=<项目名称> --title="PR标题" --body="PR描述" --base=main --head=feature-branch

# 合并 PR
/github merge pr <PR编号> --project=<项目名称>
```

### 代码库操作

```bash
# 克隆代码库
/github clone <代码库URL>

# 创建分支
/github create branch <分支名称> --project=<项目名称>

# 提交更改
/github commit --message="提交信息"

# 推送更改
/github push --branch=<分支名称>
```

## 高级功能

### 工作流自动化

```bash
# 设置自动化工作流
/github workflow create --name=<工作流名称> --trigger=<触发条件> --actions=<动作列表>

# 执行工作流
/github workflow run <工作流名称>

# 查看工作流执行状态
/github workflow status <工作流名称>
```

### 团队协作

```bash
# 管理团队成员
/github team add <用户名> --project=<项目名称> --role=<角色>
/github team remove <用户名> --project=<项目名称>

# 审核代码
/github review <PR编号> --project=<项目名称> --status=<approve|request-changes> --comment="审核评论"
```

## 配置选项

您可以通过以下命令配置 GitHub 集成：

```bash
# 设置 GitHub 个人访问令牌
/github config set token <访问令牌>

# 设置默认项目
/github config set default-project <项目名称>

# 设置默认分支
/github config set default-branch <分支名称>
```

## 常见问题

### 认证失败？

- 检查您的个人访问令牌是否有效
- 确认令牌有足够的权限
- 尝试重新设置令牌：`/github config reset token`

### 命令执行失败？

- 确认项目名称拼写正确
- 检查网络连接
- 查看详细错误信息：`/github debug last-command`

## 最佳实践

1. **使用项目别名**
   - 为常用项目设置简短别名：`/github alias set <别名> <项目完整名称>`

2. **自动化常见任务**
   - 创建工作流自动化重复性任务
   - 使用 Cron 表达式设置定时任务

3. **集成开发流程**
   - 将 GitHub 命令集成到您的开发流程中
   - 使用 VibeCopilot 的任务管理与 GitHub issue 联动

## 高级技巧

1. **批量操作**
   - 使用 `--batch` 参数处理多个项目或 issue
   - 示例：`/github close issue --batch="1,2,3,4" --project=<项目名称>`

2. **模板使用**
   - 使用预定义模板创建 issue 或 PR
   - 示例：`/github create issue --template=bug-report --project=<项目名称>`

3. **高级过滤**
   - 使用 JQ 语法过滤复杂结果
   - 示例：`/github list issues --filter=".assignee==\"username\""
