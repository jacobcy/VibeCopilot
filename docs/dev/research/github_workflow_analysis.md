# VibeCopilot GitHub 开发工作流指南

本文档提供了在 VibeCopilot 项目中使用 GitHub 进行开发的工作流指南，结合了我们的项目分析和路线图管理工具。

## 工作流概述

![工作流概览](../assets/images/workflow_overview.png)

VibeCopilot 项目采用敏捷开发方法结合 GitHub 项目管理工具，形成完整的工作流程：

1. **需求规划**：在 GitHub Project 中创建任务并规划冲刺(Sprint)
2. **开发实施**：按 Git Flow 流程开发并关联 Issues
3. **代码审查**：通过 Pull Request 进行审查和合并
4. **状态分析**：定期运行分析脚本评估项目状态
5. **路线图调整**：基于分析结果更新项目路线图

## 详细工作流程

### 1. 项目初始化

首次使用前，请确保正确设置环境变量：

```bash
export GITHUB_TOKEN=your_personal_access_token
export GITHUB_OWNER=your_github_username
export GITHUB_REPO=your_repository_name
export GITHUB_PROJECT_NUMBER=1
```

或者在项目根目录创建 `.env` 文件：

```
GITHUB_TOKEN=your_personal_access_token
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repository_name
GITHUB_PROJECT_NUMBER=1
```

### 2. 任务管理流程

#### 创建任务

1. 在 GitHub 项目中创建新 Issue：
   ```
   标题: [FEATURE] 实现用户认证功能
   描述:
   - 开发用户登录/注册接口
   - 实现JWT认证机制
   - 添加权限验证中间件
   标签: enhancement, auth
   里程碑: v1.0.0
   ```

2. 将 Issue 添加到项目看板并分配责任人

#### 处理任务

1. 将任务卡片移动到"进行中"
2. 创建功能分支：
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/ISSUE-123-user-auth
   ```

3. 开发并提交变更：
   ```bash
   git commit -m "feat(auth): 实现用户认证API [#123]"
   ```

4. 创建 Pull Request 并关联 Issue：
   ```
   标题: feat(auth): 实现用户认证功能
   描述:
   - 添加了用户登录和注册API
   - 实现了JWT令牌验证
   - 添加了相关单元测试

   Fixes #123
   ```

5. 完成代码审查后合并 PR，Issue 会自动关闭

### 3. 项目分析与路线图管理

#### 运行项目分析

我们提供了便捷的命令行工具进行项目状态分析：

```bash
# 分析项目并生成JSON格式结果
python -m scripts.github.project_cli analysis analyze \
  --metrics "progress,quality,risks" \
  --output analysis.json

# 分析项目并生成Markdown报告
python -m scripts.github.project_cli analysis analyze \
  --format markdown \
  --output project_analysis.md
```

#### 调整项目时间线

基于分析结果，可以调整项目时间线：

```bash
# 基于分析结果进行调整预览
python -m scripts.github.project_cli analysis adjust \
  --based-on-analysis analysis.json \
  --update-milestones false

# 实际应用调整
python -m scripts.github.project_cli analysis adjust \
  --based-on-analysis analysis.json \
  --update-milestones true
```

#### 自动化项目分析

我们提供了自动化脚本进行定期项目分析：

```bash
# 运行每周分析
./scripts/github/weekly_update.sh
```

运行后，分析结果将保存在 `reports/github/` 目录下：

- `analysis_YYYYMMDD.json`: 原始分析数据
- `report_YYYYMMDD.md`: Markdown格式报告
- `adjustment_YYYYMMDD.json`: 调整建议
- `suggestions_YYYYMMDD.md`: 调整建议报告

### 4. 发布管理

1. 从 `develop` 分支创建 `release` 分支：
   ```bash
   git checkout develop
   git pull
   git checkout -b release/v1.0.0
   ```

2. 运行项目分析评估风险：
   ```bash
   ./scripts/github/weekly_update.sh
   ```

3. 检查风险报告并决定是否继续发布：
   ```bash
   cat reports/github/suggestions_YYYYMMDD.md
   ```

4. 如需调整，应用时间线更新：
   ```bash
   python -m scripts.github.project_cli analysis adjust \
     --based-on-analysis reports/github/analysis_YYYYMMDD.json \
     --update-milestones true
   ```

5. 完成发布后，合并到 `main` 分支并打标签：
   ```bash
   git checkout main
   git merge release/v1.0.0
   git tag -a v1.0.0 -m "Version 1.0.0"
   git push --tags
   ```

## 最佳实践

### 提交消息规范

我们使用约定式提交规范，格式如下：

```
<type>(<scope>): <description> [#ISSUE-ID]
```

- **类型（type）**：
  - `feat`: 新功能
  - `fix`: 修复问题
  - `docs`: 文档更新
  - `style`: 代码格式调整
  - `refactor`: 代码重构
  - `test`: 添加测试
  - `chore`: 工具链或辅助工具变动

- **范围（scope）**：可选，表示变更影响的模块
- **描述（description）**：简明扼要的变更说明
- **ISSUE-ID**：关联的 GitHub Issue 编号

### 分支命名规范

- `feature/ISSUE-123-description`：新功能开发
- `bugfix/ISSUE-456-description`：问题修复
- `hotfix/ISSUE-789-description`：紧急生产修复
- `release/vX.Y.Z`：版本发布分支

### 项目分析周期建议

- 每周一次固定分析
- 每个里程碑结束时进行深度分析
- 重大变更前后进行分析
- 发现高风险时增加分析频率

## 常见问题

1. **任务无法移动？**
   - 检查你的权限设置
   - 确认任务未被锁定

2. **找不到特定任务？**
   - 使用搜索功能
   - 检查筛选器设置

3. **报告生成失败？**
   - 验证数据访问权限
   - 检查命令参数
   - 确保设置了正确的环境变量

4. **时间线调整失败？**
   - 确认有修改里程碑的权限
   - 验证分析文件格式正确
   - 检查GitHub API限制是否达到上限

## 资源链接

- [使用指南](../user/tutorials/github/usage_guide.md)
- [开发者指南](../user/tutorials/github/develop_guide.md)
- [项目分析工具文档](../user/tutorials/github/analysis_tool.md)
- [路线图管理工具文档](../user/tutorials/github/roadmap_tool.md)

---

遵循这份工作流指南，我们能够更高效地协作开发，并借助项目分析工具持续优化项目管理流程。
