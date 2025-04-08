---
title: Markdown文档语法检查工具
description: 如何使用增强版的文档语法和链接检查工具
category: 开发工具
created: 2024-06-08
updated: 2024-06-25
---

# Markdown文档语法检查工具

## 概述

VibeCopilot项目提供了增强版的Markdown文档语法检查工具，可以帮助你检查文档中的语法问题和无效链接。此工具是项目轻量级开发流程中的重要组成部分，确保文档质量和一致性。

## 特性

- **详细的错误报告**：显示问题文件、行号、列号和问题描述
- **上下文信息**：显示问题周围的代码片段，帮助快速定位问题
- **链接验证**：检查文档中的链接是否指向有效的文件
- **规则集成**：与VibeCopilot规则系统无缝集成
- **Git集成**：可作为pre-commit钩子自动执行检查

## 使用方法

### 命令行使用

检查整个docs目录：

```bash
python scripts/docs/check.py --dir=docs
```

检查特定文件：

```bash
python scripts/docs/check.py --file=docs/dev/guides/example.md
```

检查并生成报告：

```bash
python scripts/docs/check.py --dir=docs --report=report.json
```

### 输出说明

工具会生成详细的报告，包括：

1. **语法检查结果**：显示标准markdown语法问题
   ```
   文件: docs/example.md
   行号: 10, 列号: 1
   问题: MD001 - 标题层级应当逐级递增
   上下文: "# 大标题" 后直接使用 "### 三级标题"
   ```

2. **链接检查结果**：显示无效的链接
   ```
   文件: docs/example.md
   行号: 15, 列号: 3
   问题: 无效链接 - 目标文件不存在
   链接: [示例链接](missing-file.md)
   目标路径: docs/missing-file.md
   ```

## 集成到规则系统

此工具与VibeCopilot的规则系统集成，可以在规则中调用：

```markdown
# 文档检查规则

## 执行条件
当需要验证文档质量时触发

## 执行步骤
1. 调用文档检查工具
2. 分析检查结果
3. 提供修复建议

## 实现脚本
```python
import os
from scripts.docs.tools.check_links import check_markdown_links
from scripts.docs.check import check_markdown_syntax

def check_document(file_path):
    syntax_issues = check_markdown_syntax(file_path)
    link_issues = check_markdown_links(file_path)
    return syntax_issues + link_issues
```
```

## 与GitHub工作流集成

在GitHub Actions中使用此工具自动检查PR中的文档变更：

```yaml
name: Markdown Check

on:
  pull_request:
    paths:
      - '**.md'

jobs:
  check-markdown:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python scripts/docs/check.py --dir=docs
```

## 技术实现

此工具使用Python实现，主要组件包括：

- `scripts/docs/check.py`: 主入口脚本
- `scripts/docs/tools/check_links.js`: 链接检查逻辑
- `scripts/docs/tools/fix_links.js`: 链接修复工具
- `scripts/hooks/check_docs_links.js`: Git钩子集成

源代码可在项目仓库的`scripts/docs`目录中找到。

## 常见问题解决

如遇到问题，请检查：

1. 确保已安装所需Python依赖
2. 检查文档路径是否正确
3. 如果链接检查失败，可能是相对路径问题

## 未来计划

我们计划为此工具添加以下功能：

- AI辅助的自动修复建议
- 与Cursor编辑器的更深入集成
- 更多自定义规则支持

对工具有任何建议，请提交Issue或PR。
