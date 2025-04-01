---
title: Markdown文档语法检查工具
description: 如何使用增强版的文档语法和链接检查工具
category: 开发文档
created: 2024-06-08
updated: 2024-06-08
---

# Markdown文档语法检查工具

## 概述

VibeCopilot项目提供了增强版的Markdown文档语法检查工具，可以帮助你检查文档中的语法问题和无效链接。此工具会提供详细的问题报告，包括文件名、行号、问题描述和问题上下文，使你能够快速定位和修复问题。

## 特性

- **详细的错误报告**：显示问题文件、行号、列号和问题描述
- **上下文信息**：显示问题周围的代码片段，帮助快速定位问题
- **自动修复**：支持自动修复部分常见的语法问题
- **链接验证**：检查文档中的链接是否指向有效的文件
- **集成pre-commit**：可以集成到git提交流程中自动检查

## 使用方法

### 命令行使用

检查整个docs目录：

```bash
npm run check:docs
```

检查并自动修复问题：

```bash
npm run check:docs:fix
```

检查特定文件或目录：

```bash
node scripts/docs/check.js path/to/file.md
```

### 输出说明

工具会生成详细的报告，包括：

1. **语法检查结果**：显示markdownlint发现的问题
   ```
   file.md:10:1 MD001/heading-increment Heading levels should only increment by one level at a time
   ```

2. **链接检查结果**：显示无效的链接
   ```
   文件: docs/example.md
   发现 1 个无效链接:
     - [markdown] 第 15 行，第 3 列
       链接文本: "示例链接" -> missing-file.md
       目标路径: docs/missing-file.md
       内容片段: ...点击[示例链接](missing-file.md)查看更多信息...
   ```

## 语法规则说明

VibeCopilot项目使用markdownlint检查Markdown语法，主要规则包括：

- 标题层级应顺序递增
- 列表缩进应一致
- 代码块应有语言标识
- 链接应指向有效的目标
- 图片应有替代文本

完整的规则配置在项目根目录的`.markdownlint.json`文件中。

## 链接验证规则

链接检查工具会验证以下类型的链接：

- Markdown链接：`[文本](链接)`
- 图片链接：`![替代文本](图片路径)`
- HTML链接：`<a href="链接">文本</a>`
- HTML图片：`<img src="图片路径" />`

工具会自动忽略以下类型的链接：

- 外部链接 (http://, https://)
- 页内锚点 (#section)
- 邮件链接 (mailto:)
- 电话链接 (tel:)

## 集成到开发流程

在提交代码前，建议先运行检查工具确保文档没有问题：

```bash
npm run check:docs
```

如果你使用pre-commit钩子，文档语法检查会在你提交代码时自动运行。

## 故障排除

如果你遇到问题，可以尝试以下方法：

1. 确保已安装所需依赖：`npm install`
2. 检查markdownlint配置：`.markdownlint.json`
3. 使用verbose模式获取更多信息：`node scripts/docs/check.js docs --verbose`

## 技术实现

此工具结合了markdownlint和自定义的链接检查逻辑。链接检查的具体实现可以查看：

- `scripts/docs/tools/check_links.js`：链接检查逻辑
- `scripts/docs/check.js`：整合检查工具
- `scripts/hooks/check_docs_links.js`：pre-commit钩子集成
