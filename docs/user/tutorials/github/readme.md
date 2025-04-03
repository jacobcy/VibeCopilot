# VibeCopilot GitHub 项目管理助手

👋 欢迎使用 VibeCopilot 的 GitHub 项目管理工具！这是一个帮助你轻松管理项目进度的智能助手。

## 🎯 这个工具能帮你做什么？

- 📋 **可视化管理任务**：把你的想法变成清晰的任务列表
- 📅 **跟踪项目进度**：实时了解项目完成情况
- 📊 **生成进度报告**：自动生成美观的项目报告
- 🔄 **同步本地和远程**：轻松在本地和 GitHub 之间同步数据
- 📈 **项目分析评估**：智能分析项目进度、质量和风险
- ⏱️ **路线图自动调整**：根据实际进度自动优化项目时间线

## 🌟 为什么选择这个工具？

- 😊 **新手友好**：即使你不熟悉 GitHub，也能轻松上手
- 🚀 **效率提升**：自动化的工作流程，节省你的时间
- 📱 **随时掌握**：随时查看项目进展，不错过任何更新
- 🤝 **团队协作**：让团队成员轻松参与项目管理
- 🧠 **智能决策**：基于数据分析辅助项目决策

## 📚 快速开始

1. [项目初始化指南](setup_guide.md) - 从零开始设置你的项目
2. [使用说明](usage_guide.md) - 学习如何使用各项功能
3. [开发者指南](develop_guide.md) - 深入了解项目管理的最佳实践

## 🆘 需要帮助？

- 遇到问题？查看我们的[常见问题解答](../faq.md)
- 想要更多帮助？加入我们的[社区讨论](https://github.com/VibeCopilot/discussions.md)
- 发现 Bug？[提交问题](https://github.com/VibeCopilot/issues.md)

## 💡 小贴士

- 定期同步你的项目数据
- 使用直观的标签系统管理任务
- 保持任务描述简洁明了
- 及时更新任务状态
- 每周运行项目分析评估项目健康度

## 功能特点

### 路线图管理

- **导入路线图**：将本地YAML或Markdown格式的路线图数据导入到GitHub Projects
- **导出路线图**：从GitHub Projects导出路线图数据为YAML或JSON格式
- **生成报告**：生成可视化的路线图报告，支持HTML、Markdown和JSON格式

### 项目分析

- **进度分析**：评估项目完成率和时间进度偏差
- **质量分析**：监控PR合并率和代码审查质量
- **风险评估**：识别阻塞任务和延期风险

### 路线图调整

- **自动调整**：根据实际进度自动调整里程碑时间线
- **调整建议**：生成智能化的项目调整建议
- **变更跟踪**：记录和验证所有时间线调整

## 安装

确保已安装Python 3.7+和所需依赖：

```bash
# 克隆仓库
git clone https://github.com/yourusername/VibeCopilot.git
cd VibeCopilot

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 环境变量设置

设置GitHub个人访问令牌：

```bash
export GITHUB_TOKEN=your_personal_access_token
export GITHUB_OWNER=your_github_username
export GITHUB_REPO=your_repository_name
export GITHUB_PROJECT_NUMBER=1
```

### 导入路线图

将本地路线图数据导入到GitHub Projects：

```bash
python -m src.github.projects.main import \
  --file path/to/roadmap.yaml \
  --owner github_username \
  --repo repository_name
```

支持的格式：

- YAML格式（.yaml, .yml）
- Markdown格式（.md, .markdown）

### 生成路线图报告

从GitHub Projects生成路线图报告：

```bash
python -m src.github.projects.main generate \
  --owner github_username \
  --repo repository_name \
  --project-number 1 \
  --output-dir ./outputs
```

### 项目分析与路线图调整

分析项目状态并生成报告：

```bash
# 分析项目并生成报告
python -m scripts.github.project_cli analysis analyze \
  --owner github_username \
  --repo repository_name \
  --project-number 1 \
  --format markdown \
  --output project_analysis.md

# 根据分析结果调整时间线
python -m scripts.github.project_cli analysis adjust \
  --based-on-analysis analysis.json \
  --update-milestones true
```

### 自动化项目管理

使用提供的自动化脚本定期分析项目状态：

```bash
# 设置每周自动分析
./scripts/github/weekly_update.sh
```

## 数据格式

### YAML路线图示例

```yaml
title: "产品路线图"
description: "我们产品的发展规划"
milestones:
  - id: "M1"
    name: "MVP原型版"
    description: "最小可行产品版本"
    status: "completed"
    start_date: "2023-05-01"
    end_date: "2023-06-30"
    tasks:
      - id: "M1-1"
        title: "设计产品架构"
        description: "定义产品架构"
        milestone: "M1"
        status: "completed"
        priority: "P1"
```

### Markdown路线图示例

```markdown
# 产品路线图

我们产品的发展规划

## 🏁 MVP原型版 (2023-05-01 ~ 2023-06-30)

- ✅ 设计产品架构
- ✅ 实现基础框架
- ✅ 开发核心功能
```

让我们开始使用这个强大的工具，让项目管理变得更简单、更有趣！🚀
