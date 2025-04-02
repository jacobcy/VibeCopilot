# GitHub 项目管理工具使用指南

本文档详细介绍如何使用 VibeCopilot 提供的 GitHub 项目管理工具，帮助您有效管理项目进度、分析项目健康状况并调整项目时间线。

## 前提条件

在开始使用前，请确保：

1. 已安装Python 3.8+
2. 已安装必要的依赖：`pip install -r scripts/github/requirements.txt`
3. 配置了GitHub API访问权限

## 配置GitHub令牌

首先，您需要设置GitHub个人访问令牌：

1. 访问GitHub [Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. 点击"Generate new token"
3. 勾选以下权限：
   - `repo` (完整仓库访问权限)
   - `project` (项目管理权限)
   - `read:org` (如果是组织仓库)

然后，设置环境变量：

```bash
export GITHUB_TOKEN=your_personal_access_token
export GITHUB_OWNER=your_github_username_or_org
export GITHUB_REPO=your_repository_name
export GITHUB_PROJECT_NUMBER=1  # 项目编号，从URL获取
```

或者创建`.env`文件：

```
GITHUB_TOKEN=your_personal_access_token
GITHUB_OWNER=your_github_username_or_org
GITHUB_REPO=your_repository_name
GITHUB_PROJECT_NUMBER=1
```

## 基本用法

### 项目分析工具

#### 进行项目状态分析

```bash
# 基本用法 - JSON输出
python -m scripts.github.project_cli analysis analyze \
  --metrics "progress,quality,risks"

# 生成Markdown报告
python -m scripts.github.project_cli analysis analyze \
  --format markdown \
  --output project_analysis.md

# 指定特定项目
python -m scripts.github.project_cli analysis analyze \
  --owner MyOrg \
  --repo MyProject \
  --project-number 2 \
  --metrics "progress,velocity,risks" \
  --output analysis.json
```

#### 生成项目报告

```bash
# 从分析结果生成报告
python -m scripts.github.project_cli analysis report \
  --input analysis.json \
  --format markdown \
  --output project_report.md
```

#### 调整项目时间线

```bash
# 预览调整建议
python -m scripts.github.project_cli analysis adjust \
  --based-on-analysis analysis.json \
  --update-milestones false \
  --output adjustment_preview.json

# 应用调整到GitHub
python -m scripts.github.project_cli analysis adjust \
  --based-on-analysis analysis.json \
  --update-milestones true
```

### 自动化工作流

您可以使用提供的自动化脚本执行周期性项目分析：

```bash
# 运行每周分析和报告
./scripts/github/weekly_update.sh
```

该脚本会：

1. 分析当前项目状态
2. 生成详细报告
3. 提供调整建议
4. 保存所有结果到`reports/github/`目录

### 报告结构

项目分析报告包含以下关键部分：

1. **项目概览**：总体进度、健康状况评分
2. **进度指标**：任务完成率、速度、偏差
3. **质量指标**：代码质量、测试覆盖率、文档完整性
4. **风险评估**：潜在延迟、依赖项风险、资源约束
5. **建议**：时间线调整、资源分配、优先级调整

## 高级功能

### 自定义分析指标

您可以创建自定义分析指标：

```bash
python -m scripts.github.project_cli analysis analyze \
  --metrics "progress,quality,risks" \
  --custom-metrics-file my_metrics.json
```

自定义指标文件格式示例：

```json
{
  "custom_metric_name": {
    "type": "composite",
    "components": ["progress", "quality"],
    "weights": [0.7, 0.3],
    "description": "自定义项目健康指标"
  }
}
```

### 集成到CI/CD流程

将项目分析集成到CI/CD流程：

```yaml
# .github/workflows/project-analysis.yml
name: Project Analysis

on:
  schedule:
    - cron: '0 9 * * 1'  # 每周一上午9点

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r scripts/github/requirements.txt
      - name: Run project analysis
        run: ./scripts/github/weekly_update.sh
        env:
          GITHUB_TOKEN: ${{ secrets.GH_PROJECT_TOKEN }}
          GITHUB_OWNER: ${{ github.repository_owner }}
          GITHUB_REPO: ${{ github.repository }}
          GITHUB_PROJECT_NUMBER: 1
      - name: Archive reports
        uses: actions/upload-artifact@v2
        with:
          name: project-reports
          path: reports/github/
```

## 常见问题解答

### 常见错误及解决方案

1. **API权限错误**
   - 问题：`401 Unauthorized` 或 `403 Forbidden`
   - 解决：检查GitHub令牌权限是否正确，确认令牌未过期

2. **找不到项目**
   - 问题：`Project with number X not found`
   - 解决：确认项目编号是否正确，检查您是否有该项目的访问权限

3. **速度过慢**
   - 问题：分析过程耗时长
   - 解决：使用`--fields`参数限制获取的字段，或使用`--max-items`限制处理的项目数量

4. **调整失败**
   - 问题：时间线调整未应用
   - 解决：确认您有编辑里程碑的权限，检查`--update-milestones`是否设为`true`

### 提示和技巧

1. **定期分析**：设置每周自动分析以持续监控项目健康状况
2. **差异比较**：保存历史报告以比较不同时间点的项目状态
3. **组合报告**：对多个相关项目进行分析并生成综合报告
4. **预警阈值**：设置关键指标阈值，当超过时发送通知
5. **团队共享**：在团队会议中分享分析报告，共同制定改进计划

## 附录

### 可用分析指标

| 指标名称 | 描述 | 类型 |
|---------|------|------|
| progress | 项目总体进度 | 复合指标 |
| velocity | 团队开发速度 | 单一指标 |
| quality | 代码和文档质量 | 复合指标 |
| risks | 项目风险评估 | 复合指标 |
| timeline | 时间线准确性 | 单一指标 |
| resources | 资源分配情况 | 复合指标 |

### 命令行参数参考

```
项目分析命令:
  --metrics TEXT               要计算的指标列表(逗号分隔)
  --owner TEXT                 GitHub仓库所有者
  --repo TEXT                  GitHub仓库名称
  --project-number INTEGER     GitHub项目编号
  --format [json|markdown|html]  输出格式
  --output TEXT                输出文件路径
  --fields TEXT                要获取的字段(逗号分隔)
  --max-items INTEGER          最大处理项目数
  --custom-metrics-file TEXT   自定义指标配置文件

时间线调整命令:
  --based-on-analysis TEXT     分析结果文件路径
  --update-milestones BOOLEAN  是否更新GitHub里程碑
  --adjustment-factor FLOAT    调整系数(默认:1.2)
  --only-future BOOLEAN        是否只调整未来里程碑
  --output TEXT                输出文件路径
```

## 相关资源

- [开发者指南](./develop_guide.md) - 如何扩展和定制项目管理工具
- [GitHub工作流指南](../../workflow/github_workflow.md) - VibeCopilot项目的GitHub工作流程
- [路线图工具文档](./roadmap_tool.md) - 项目路线图生成和管理工具
- [分析工具文档](./analysis_tool.md) - 项目分析工具的技术文档
