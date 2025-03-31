# GitHub Projects 使用指南

## 简介

GitHub Projects 是一个用于跟踪和管理项目任务的工具，在VibeCopilot中，我们使用它来管理开发路线图。本指南将介绍如何利用GitHub Projects进行高效的项目管理。

## 基本概念

- **项目板(Project Board)**: 一个可视化的任务管理面板
- **任务(Item)**: 项目中的一个工作单元，可以是Issue或Pull Request
- **字段(Field)**: 任务的属性，如状态、优先级、里程碑等
- **视图(View)**: 展示任务的不同方式，如看板视图、表格视图等

## 设置GitHub Projects

### 1. 创建新项目

使用VibeCopilot脚本创建项目:

```bash
python scripts/github/create_project.py --owner username --repo reponame --name "项目名称" --description "项目描述"
```

或手动创建:
1. 访问GitHub仓库
2. 点击"Projects"选项卡
3. 点击"New project"按钮
4. 选择"Board"模板
5. 填写项目名称和描述

### 2. 配置字段

标准字段配置:

- **状态(Status)**:
  - Todo: 待开发
  - In Progress: 开发中
  - In Review: 审核中
  - Done: 已完成

- **优先级(Priority)**:
  - P0: 关键
  - P1: 高
  - P2: 中
  - P3: 低

- **里程碑(Milestone)**:
  - M1: 第一里程碑
  - M2: 第二里程碑
  - M3: 第三里程碑
  - ...

- **类型(Type)**:
  - Feature: 新功能
  - Bug: 缺陷修复
  - Task: 一般任务
  - Doc: 文档工作

## 使用VibeCopilot脚本管理Projects

VibeCopilot提供了一系列脚本，简化GitHub Projects的管理:

### 导入路线图

将路线图从Markdown文档导入到GitHub Projects:

```bash
python scripts/github/import_roadmap_to_github.py --file docs/project/roadmap/development_roadmap.md --owner username --repo reponame --project-number 1
```

### 添加Issues到项目

创建Issue并添加到项目:

```bash
python scripts/github/add_issues_to_project.py --owner username --repo reponame --project-number 1 --issue-title "实现功能X" --issue-body "详细描述..." --labels "feature,P1" --milestone "M1"
```

### 更新项目状态

更新项目进度和状态:

```bash
python scripts/github/update_project_status.py --owner username --repo reponame --project-number 1 --item-id issue_id --status "In Progress"
```

### 生成报告

生成项目进度报告:

```bash
python scripts/github/generate_project_report.py --owner username --repo reponame --project-number 1 --output report.md
```

## 最佳实践

### 1. 项目管理流程

1. **规划阶段**:
   - 创建项目板
   - 导入路线图
   - 设置里程碑和标签

2. **开发阶段**:
   - 创建Issue并关联到项目
   - 按优先级处理任务
   - 使用分支命名约定: `feature/issue-number-short-description`

3. **审核阶段**:
   - 创建Pull Request并关联Issue
   - 使用关键词自动关联: `Fixes #123`
   - 进行代码审核

4. **完成阶段**:
   - 合并PR
   - 更新任务状态
   - 生成进度报告

### 2. 项目视图使用

- **看板视图**: 日常任务管理
- **表格视图**: 整体项目状态查看
- **路线图视图**: 时间线和进度跟踪

### 3. 标签使用策略

使用前缀区分不同类型的标签:
- `type:` - 任务类型 (feature, bug, doc)
- `priority:` - 优先级 (P0-P3)
- `status:` - 状态 (blocked, needs-review)
- `area:` - 功能领域 (frontend, backend, api)

## 故障排除

常见问题及解决方案:

1. **API限制**:
   - 使用个人访问令牌增加限额
   - 实现请求间隔和重试逻辑

2. **权限问题**:
   - 确保令牌有足够权限(`repo`, `project`)
   - 检查用户在组织中的角色

3. **数据不同步**:
   - 手动验证更新状态
   - 使用`update_project_data.py`脚本重新同步

## 资源链接

- [GitHub Projects 官方文档](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)
- [GitHub GraphQL API 文档](https://docs.github.com/en/graphql)
- [VibeCopilot GitHub脚本文档](../scripts/github/README.md)

---

通过本指南和VibeCopilot提供的工具，您可以高效地使用GitHub Projects管理开发过程，确保项目按计划有序进行。
