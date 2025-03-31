---
title: Obsidian语法检查工具
description: 统一MD语法检查与Obsidian特定语法验证工具的使用指南
category: 开发文档
created: 2024-04-05
updated: 2024-04-05
---

# Obsidian语法检查工具使用指南

## 概述

本文档介绍Obsidian语法检查工具的使用方法和配置，解决pre-commit与sync.py之间的语法检查一致性问题。该工具专门用于检查Obsidian特有的语法结构，如双向链接、嵌入图片和MDX组件等。

## 功能特性

1. **专用语法检查**：
   - Obsidian双向链接 `[文件名](文件名.md)` 和 `[显示文本](文件名.md)`
   - Obsidian嵌入 `![文件名](文件名.md)`
   - MDX语法检查（未闭合组件、数字开头标签等）

2. **多级错误处理**：
   - 错误（Errors）：需要修复的严重问题
   - 警告（Warnings）：建议修复的问题
   - 信息（Info）：提示性问题

3. **集成模式**：
   - pre-commit钩子自动检查
   - sync.py集成检查
   - 命令行独立检查

## 使用方法

### 命令行直接使用

检查单个文件：
```bash
python scripts/docs/utils/obsidian/syntax_checker.py path/to/file.md
```

检查整个目录：
```bash
python scripts/docs/utils/obsidian/syntax_checker.py docs/
```

生成详细HTML报告：
```bash
python scripts/docs/utils/generate_report.py --docs-dir docs/ --format html --output report.html
```

### 与sync.py结合使用

检查语法但不执行同步：
```bash
python scripts/docs/obsidian/sync.py --check-syntax
```

严格模式（语法错误会阻止同步）：
```bash
python scripts/docs/obsidian/sync.py --sync-file path/to/file.md --strict
```

非严格模式（只报警告，继续同步）：
```bash
python scripts/docs/obsidian/sync.py --sync-file path/to/file.md
```

## 工作原理

### 1. 检查流程

1. 解析Markdown文件
2. 使用正则表达式匹配特定语法结构
3. 验证链接目标是否存在
4. 检查MDX组件完整性
5. 验证YAML前置元数据

### 2. 与pre-commit集成

pre-commit钩子配置（位于`.pre-commit-config.yaml`）：

```yaml
-   repo: local
    hooks:
    -   id: obsidian-syntax-check
        name: Obsidian syntax checker
        description: "Checks Obsidian documents for specific syntax issues"
        entry: python scripts/hooks/check_obsidian_syntax.py
        language: python
        types: [markdown]
        files: '^docs/'
        verbose: true
        stages: [commit]
```

### 3. 与sync.py集成

sync.py在执行同步前会先检查语法问题：

- 非严格模式下：报告问题但继续同步
- 严格模式下：发现问题会终止同步

## 常见问题与解决方案

### 链接错误问题

**问题**：报告"链接目标不存在"但文件确实存在
**解决方案**：

1. 检查文件名大小写是否一致
2. 检查是否使用了带空格的文件名（应使用下划线替代）
3. 验证链接格式是否正确

### MDX组件问题

**问题**：报告Tabs组件未闭合
**解决方案**：

1. 确保每个`<Tabs>`都有对应的`</Tabs>`结束标签
2. 检查嵌套组件的闭合顺序是否正确

### 前置元数据问题

**问题**：缺少必要的元数据字段
**解决方案**：
确保每个文档都包含以下前置元数据：
```yaml
---
title: 文档标题
description: 文档描述
category: 文档分类
created: 创建日期
updated: 更新日期
---
```

## 配置选项

### syntax_checker.py配置参数

| 参数 | 说明 |
|------|------|
| path | 要检查的文件或目录路径 |
| --base-dir | 文档基础目录 |
| --recursive | 递归检查子目录 |
| --verbose | 输出详细日志 |
| --json | 以JSON格式输出结果 |
| --errors-only | 只报告错误，忽略警告和提示 |

### generate_report.py配置参数

| 参数 | 说明 |
|------|------|
| --docs-dir | 文档目录路径 |
| --format | 报告格式（html/json/text） |
| --output | 输出文件路径 |
| --include-info | 包含信息级别的提示 |

## 最佳实践

1. **定期运行完整检查**：
   ```bash
   python scripts/docs/utils/generate_report.py
   ```

2. **提交前自动检查**：
   pre-commit会自动运行检查，确保提交前已解决主要问题

3. **在CI/CD管道中集成**：
   GitHub Actions中添加语法检查步骤，确保团队协作时保持语法一致性

4. **处理优先级**：
   - 首先修复所有错误级别问题
   - 然后处理警告级别问题
   - 根据需要处理信息级别问题

## 未来计划

1. 添加自动修复功能，类似于现有的链接修复
2. 扩展检查范围，支持更多Obsidian特有语法
3. 改进报告系统，提供更直观的问题展示

## 相关文档

- [文档引擎使用指南](../user/docs_engine_guide.md)
- [Obsidian最佳实践](../user/obsidian_best_practices.md)
- [Markdown语法规范](../dev/markdown_style_guide.md)
